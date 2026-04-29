package main

// borrowed from from https://github.com/caddyserver/forwardproxy/blob/master/httpclient/httpclient.go
import (
	"bufio"
	"context"
	"crypto/tls"
	"encoding/base64"

	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"strconv"
	"sync"
	"time"

	http "github.com/Danny-Dasilva/fhttp"
	http2 "github.com/Danny-Dasilva/fhttp/http2"
	"golang.org/x/net/proxy"
	"h12.io/socks"
)

type SocksDialer struct {
	socksDial func(string, string) (net.Conn, error)
}

func (d *SocksDialer) DialContext(_ context.Context, network, addr string) (net.Conn, error) {
	return d.socksDial(network, addr)
}

func (d *SocksDialer) Dial(network, addr string) (net.Conn, error) {
	return d.socksDial(network, addr)
}

// socks4ContextDialer is a minimal SOCKS4 client that uses a configurable
// underlying TCP dialer (so net.Dialer.LocalAddr / context cancellation are
// honored on the client->proxy connection). h12.io/socks's DialSocksProxy
// always uses net.DialTimeout internally with no LocalAddr support, so we
// implement the SOCKS4 handshake here when localAddress binding is required.
//
// Wire format (RFC 1928 predecessor): VN=4, CD=1 (CONNECT), DSTPORT (BE u16),
// DSTIP (4 bytes), USERID (empty + null terminator). Server replies 8 bytes;
// resp[1]==0x5A means request granted.
type socks4ContextDialer struct {
	proxyAddr string      // host:port of the SOCKS4 proxy
	dialer    *net.Dialer // TCP dialer; carries LocalAddr when set
}

func (d *socks4ContextDialer) DialContext(ctx context.Context, network, addr string) (net.Conn, error) {
	conn, err := d.dialer.DialContext(ctx, "tcp", d.proxyAddr)
	if err != nil {
		return nil, err
	}
	// On any handshake failure, close the conn we just opened.
	defer func() {
		if err != nil {
			_ = conn.Close()
		}
	}()

	// Resolve target host to IPv4 (SOCKS4 has no hostname field; SOCKS4A
	// would, but the previous h12.io/socks SOCKS4 path also resolves locally).
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		return nil, err
	}
	port, err := strconv.Atoi(portStr)
	if err != nil {
		return nil, fmt.Errorf("invalid port %q: %w", portStr, err)
	}
	if port < 0 || port > 0xFFFF {
		return nil, fmt.Errorf("port out of range: %d", port)
	}

	var ip4 net.IP
	if parsed := net.ParseIP(host); parsed != nil {
		ip4 = parsed.To4()
	}
	if ip4 == nil {
		ips, lerr := net.DefaultResolver.LookupIPAddr(ctx, host)
		if lerr != nil {
			return nil, lerr
		}
		for _, ia := range ips {
			if v4 := ia.IP.To4(); v4 != nil {
				ip4 = v4
				break
			}
		}
		if ip4 == nil {
			return nil, fmt.Errorf("no IPv4 address found for %q", host)
		}
	}

	req := []byte{
		0x04,                        // VN
		0x01,                        // CD = CONNECT
		byte(port >> 8), byte(port), // DSTPORT (big-endian)
		ip4[0], ip4[1], ip4[2], ip4[3], // DSTIP
		0x00, // USERID = empty + null terminator
	}

	if dl, ok := ctx.Deadline(); ok {
		_ = conn.SetDeadline(dl)
	}

	if _, err = conn.Write(req); err != nil {
		return nil, err
	}

	resp := make([]byte, 8)
	if _, err = io.ReadFull(conn, resp); err != nil {
		return nil, err
	}
	if resp[0] != 0x00 {
		err = fmt.Errorf("socks4: malformed reply, first byte %#x not zero", resp[0])
		return nil, err
	}
	switch resp[1] {
	case 0x5A:
		// granted
	case 0x5B:
		err = errors.New("socks4: connection request rejected or failed")
		return nil, err
	case 0x5C:
		err = errors.New("socks4: rejected because SOCKS server cannot connect to identd on the client")
		return nil, err
	case 0x5D:
		err = errors.New("socks4: rejected because client and identd report different user-ids")
		return nil, err
	default:
		err = fmt.Errorf("socks4: unknown reply code %#x", resp[1])
		return nil, err
	}

	// Clear the deadline before returning.
	if cerr := conn.SetDeadline(time.Time{}); cerr != nil {
		err = cerr
		return nil, err
	}

	return conn, nil
}

func (d *socks4ContextDialer) Dial(network, addr string) (net.Conn, error) {
	return d.DialContext(context.Background(), network, addr)
}

// connectDialer allows to configure one-time use HTTP CONNECT client
type connectDialer struct {
	ProxyURL      url.URL
	DefaultHeader http.Header

	Dialer proxy.ContextDialer // overridden dialer allow to control establishment of TCP connection

	// overridden DialTLS allows user to control establishment of TLS connection
	// MUST return connection with completed Handshake, and NegotiatedProtocol
	DialTLS func(network string, address string) (net.Conn, string, error)

	// tlsDialer holds the underlying net.Dialer used when this connectDialer
	// must establish a TLS connection to an https:// proxy. It carries
	// LocalAddr (when set) so the client->proxy TCP socket binds the chosen
	// local IP. tls.Dial does not consult any net.Dialer, which is why we
	// need a separate field rather than reusing Dialer (which is a
	// proxy.ContextDialer interface — possibly a SOCKS wrapper).
	tlsDialer *net.Dialer

	EnableH2ConnReuse  bool
	cacheH2Mu          sync.Mutex
	cachedH2ClientConn *http2.ClientConn
	cachedH2RawConn    net.Conn
}

// newConnectDialer creates a dialer to issue CONNECT requests and tunnel traffic via HTTP/S proxy.
// proxyUrlStr must provide Scheme and Host, may provide credentials and port.
// Example: https://username:password@golang.org:443
// localAddress optionally binds the outgoing TCP connection to the given local IP.
// The bind applies to the client->proxy hop only (the proxy opens its own
// socket to the destination), so the destination server never observes
// localAddress when a proxy is in the path. Only the proxy and any on-path
// observer between client and proxy see this IP.
func newConnectDialer(proxyURLStr string, UserAgent string, localAddress string) (proxy.ContextDialer, error) {
	proxyURL, err := url.Parse(proxyURLStr)
	if err != nil {
		return nil, err
	}

	if proxyURL.Host == "" || proxyURL.Host == "undefined" {
		return nil, errors.New("invalid url `" + proxyURLStr +
			"`, make sure to specify full url like https://username:password@hostname.com:443/")
	}

	client := &connectDialer{
		ProxyURL:          *proxyURL,
		DefaultHeader:     make(http.Header),
		EnableH2ConnReuse: true,
	}

	// baseDialer is the underlying TCP dialer for the client->proxy hop.
	// When localAddress is set it carries LocalAddr so the kernel binds the
	// outbound socket to the chosen IP. We construct it BEFORE the scheme
	// switch so SOCKS branches can plumb it through their forward / proxy
	// dial hooks (the original code put this block AFTER the SOCKS early
	// returns, silently dropping localAddress for SOCKS proxies).
	baseDialer := &net.Dialer{}
	if localAddress != "" {
		if ip := net.ParseIP(localAddress); ip != nil {
			baseDialer.LocalAddr = &net.TCPAddr{IP: ip}
		}
	}
	client.tlsDialer = baseDialer

	switch proxyURL.Scheme {
	case "http":
		if proxyURL.Port() == "" {
			proxyURL.Host = net.JoinHostPort(proxyURL.Host, "80")
		}
	case "https":
		if proxyURL.Port() == "" {
			proxyURL.Host = net.JoinHostPort(proxyURL.Host, "443")
		}
	case "socks5", "socks5h":
		var auth *proxy.Auth
		if proxyURL.User != nil {
			if proxyURL.User.Username() != "" {
				username := proxyURL.User.Username()
				password, _ := proxyURL.User.Password()
				auth = &proxy.Auth{User: username, Password: password}
			}
		}
		// Use baseDialer (LocalAddr-aware when set) as the forward dialer so
		// proxy.SOCKS5 invokes it for the TCP connect to the SOCKS5 proxy.
		// For socks5h the original code used proxy.Direct; baseDialer is a
		// strict superset (zero-value net.Dialer behaves like Direct when
		// localAddress is empty).
		var forward proxy.Dialer = baseDialer
		dialSocksProxy, err := proxy.SOCKS5("tcp", proxyURL.Host, auth, forward)
		if err != nil {
			return nil, fmt.Errorf("Error creating SOCKS5 proxy, reason %s", err)
		}
		if contextDialer, ok := dialSocksProxy.(proxy.ContextDialer); ok {
			client.Dialer = contextDialer
		} else {
			return nil, errors.New("failed type assertion to DialContext")
		}
		client.DefaultHeader.Set("User-Agent", UserAgent)
		return client, nil
	case "socks4":
		// h12.io/socks does not expose a forward-dialer hook, so when
		// localAddress is set we use a custom SOCKS4 client that dials the
		// proxy via baseDialer (with LocalAddr) and performs the SOCKS4
		// handshake manually. Otherwise we keep the original h12.io/socks
		// path so the default behavior is unchanged.
		if localAddress != "" {
			client.Dialer = &socks4ContextDialer{
				proxyAddr: proxyURL.Host,
				dialer:    baseDialer,
			}
		} else {
			dialer := &SocksDialer{socks.DialSocksProxy(socks.SOCKS4, proxyURL.Host)}
			client.Dialer = dialer
		}
		client.DefaultHeader.Set("User-Agent", UserAgent)
		return client, nil
	case "":
		return nil, errors.New("specify scheme explicitly (https://)")
	default:
		return nil, errors.New("scheme " + proxyURL.Scheme + " is not supported")
	}

	client.Dialer = baseDialer

	if proxyURL.User != nil {
		if proxyURL.User.Username() != "" {
			// password, _ := proxyUrl.User.Password()
			// transport.DefaultHeader.Set("Proxy-Authorization", "Basic "+
			// 	base64.StdEncoding.EncodeToString([]byte(proxyUrl.User.Username()+":"+password)))

			username := proxyURL.User.Username()
			password, _ := proxyURL.User.Password()

			// transport.DefaultHeader.SetBasicAuth(username, password)
			auth := username + ":" + password
			basicAuth := "Basic " + base64.StdEncoding.EncodeToString([]byte(auth))
			client.DefaultHeader.Add("Proxy-Authorization", basicAuth)
		}
	}
	client.DefaultHeader.Set("User-Agent", UserAgent)
	return client, nil
}

func (c *connectDialer) Dial(network, address string) (net.Conn, error) {
	return c.DialContext(context.Background(), network, address)
}

// ContextKeyHeader Users of context.WithValue should define their own types for keys
type ContextKeyHeader struct{}

// ctx.Value will be inspected for optional ContextKeyHeader{} key, with `http.Header` value,
// which will be added to outgoing request headers, overriding any colliding c.DefaultHeader
func (c *connectDialer) DialContext(ctx context.Context, network, address string) (net.Conn, error) {
	if c.ProxyURL.Scheme == "socks5" || c.ProxyURL.Scheme == "socks4" || c.ProxyURL.Scheme == "socks5h" {
		return c.Dialer.DialContext(ctx, network, address)
	}

	req := (&http.Request{
		Method: "CONNECT",
		URL:    &url.URL{Host: address},
		Header: make(http.Header),
		Host:   address,
	}).WithContext(ctx)
	for k, v := range c.DefaultHeader {
		req.Header[k] = v
	}
	if ctxHeader, ctxHasHeader := ctx.Value(ContextKeyHeader{}).(http.Header); ctxHasHeader {
		for k, v := range ctxHeader {
			req.Header[k] = v
		}
	}
	connectHTTP2 := func(rawConn net.Conn, h2clientConn *http2.ClientConn) (net.Conn, error) {
		req.Proto = "HTTP/2.0"
		req.ProtoMajor = 2
		req.ProtoMinor = 0
		pr, pw := io.Pipe()
		req.Body = pr

		resp, err := h2clientConn.RoundTrip(req)
		if err != nil {
			_ = rawConn.Close()
			return nil, err
		}

		if resp.StatusCode != http.StatusOK {
			_ = rawConn.Close()
			return nil, errors.New("Proxy responded with non 200 code: " + resp.Status + "StatusCode:" + strconv.Itoa(resp.StatusCode))
		}
		return newHTTP2Conn(rawConn, pw, resp.Body), nil
	}

	connectHTTP1 := func(rawConn net.Conn) (net.Conn, error) {
		req.Proto = "HTTP/1.1"
		req.ProtoMajor = 1
		req.ProtoMinor = 1

		err := req.Write(rawConn)
		if err != nil {
			_ = rawConn.Close()
			return nil, err
		}

		resp, err := http.ReadResponse(bufio.NewReader(rawConn), req)
		if err != nil {
			_ = rawConn.Close()
			return nil, err
		}

		if resp.StatusCode != http.StatusOK {
			_ = rawConn.Close()
			return nil, errors.New("Proxy responded with non 200 code: " + resp.Status + " StatusCode:" + strconv.Itoa(resp.StatusCode))
		}
		return rawConn, nil
	}

	if c.EnableH2ConnReuse {
		c.cacheH2Mu.Lock()
		unlocked := false
		if c.cachedH2ClientConn != nil && c.cachedH2RawConn != nil {
			if c.cachedH2ClientConn.CanTakeNewRequest() {
				rc := c.cachedH2RawConn
				cc := c.cachedH2ClientConn
				c.cacheH2Mu.Unlock()
				unlocked = true
				proxyConn, err := connectHTTP2(rc, cc)
				if err == nil {
					return proxyConn, err
				}
				// else: carry on and try again
			}
		}
		if !unlocked {
			c.cacheH2Mu.Unlock()
		}
	}

	var err error
	var rawConn net.Conn
	negotiatedProtocol := ""
	switch c.ProxyURL.Scheme {
	case "http":
		rawConn, err = c.Dialer.DialContext(ctx, network, c.ProxyURL.Host)
		if err != nil {
			return nil, err
		}
	case "https":
		if c.DialTLS != nil {
			rawConn, negotiatedProtocol, err = c.DialTLS(network, c.ProxyURL.Host)
			if err != nil {
				return nil, err
			}
		} else {
			tlsConf := tls.Config{
				NextProtos:         []string{"h2", "http/1.1"},
				ServerName:         c.ProxyURL.Hostname(),
				InsecureSkipVerify: true,
			}
			// Dial the underlying TCP via the LocalAddr-aware net.Dialer
			// (c.tlsDialer) so the client->proxy socket honors localAddress,
			// then wrap in tls.Client and complete the handshake. The
			// previous tls.Dial(...) path bypassed any custom Dialer and
			// silently dropped localAddress for HTTPS proxies.
			netDialer := c.tlsDialer
			if netDialer == nil {
				netDialer = &net.Dialer{}
			}
			plainConn, derr := netDialer.DialContext(ctx, network, c.ProxyURL.Host)
			if derr != nil {
				return nil, derr
			}
			tlsConn := tls.Client(plainConn, &tlsConf)
			if herr := tlsConn.HandshakeContext(ctx); herr != nil {
				_ = plainConn.Close()
				return nil, herr
			}
			negotiatedProtocol = tlsConn.ConnectionState().NegotiatedProtocol
			rawConn = tlsConn
		}
	default:
		return nil, errors.New("scheme " + c.ProxyURL.Scheme + " is not supported")
	}

	switch negotiatedProtocol {
	case "":
		fallthrough
	case "http/1.1":
		return connectHTTP1(rawConn)
	case "h2":
		//TODO: update this with correct navigator
		t := http2.Transport{Navigator: "chrome"}
		h2clientConn, err := t.NewClientConn(rawConn)
		if err != nil {
			_ = rawConn.Close()
			return nil, err
		}

		proxyConn, err := connectHTTP2(rawConn, h2clientConn)
		if err != nil {
			_ = rawConn.Close()
			return nil, err
		}
		if c.EnableH2ConnReuse {
			c.cacheH2Mu.Lock()
			c.cachedH2ClientConn = h2clientConn
			c.cachedH2RawConn = rawConn
			c.cacheH2Mu.Unlock()
		}
		return proxyConn, err
	default:
		_ = rawConn.Close()
		return nil, errors.New("negotiated unsupported application layer protocol: " +
			negotiatedProtocol)
	}
}

func newHTTP2Conn(c net.Conn, pipedReqBody *io.PipeWriter, respBody io.ReadCloser) net.Conn {
	return &http2Conn{Conn: c, in: pipedReqBody, out: respBody}
}

type http2Conn struct {
	net.Conn
	in  *io.PipeWriter
	out io.ReadCloser
}

func (h *http2Conn) Read(p []byte) (n int, err error) {
	return h.out.Read(p)
}

func (h *http2Conn) Write(p []byte) (n int, err error) {
	return h.in.Write(p)
}

func (h *http2Conn) Close() error {
	var retErr error = nil
	if err := h.in.Close(); err != nil {
		retErr = err
	}
	if err := h.out.Close(); err != nil {
		retErr = err
	}
	return retErr
}

func (h *http2Conn) CloseConn() error {
	return h.Conn.Close()
}

func (h *http2Conn) CloseWrite() error {
	return h.in.Close()
}

func (h *http2Conn) CloseRead() error {
	return h.out.Close()
}
