# Release Process

1. Create a release branch from current `main`.
2. Update the version in both `pyproject.toml` and `cycletls/__version__.py`.
3. Run `uv lock` to refresh the package version in `uv.lock`.
4. Move the changelog's unreleased entries under the new version and date.
5. Validate the version, tests and package build, then open a version-bump PR.
6. For a cross-platform build check, manually run **Build and Release** on the
   release branch. A manual branch run builds artifacts without publishing.
7. Merge the PR into `main`, then tag that merged commit:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v0.0.5 -m "Release v0.0.5"
   git push origin refs/tags/v0.0.5
   ```

   Substitute the actual version. Use the repository owner's GitHub credentials
   for the push.

Pushing a tag matching `v*.*.*` triggers `.github/workflows/release.yml`. It builds
Linux, macOS and Windows wheels plus a source distribution, publishes them to
PyPI using the `pypi` environment's trusted publisher, then creates a GitHub
release with those assets and generated notes. The tag does not set the Python
package version; the version files must already match it.

The workflow validates that each wheel includes a loadable native library with
the required FFI exports and that the source archive stays below PyPI's file
limit. A successful build alone does not establish that a wheel contains Go.

## Fixing a failed release

Inspect the failed job before retrying. If publication has not started, fix the
build and validate the release branch first. If any files have already been
published to PyPI, use a new package version for changed artifacts. Do not move
an already published release tag or delete unrelated tags.
