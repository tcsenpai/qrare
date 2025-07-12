#!/bin/sh

# This script installs Eget.
#
# Quick install: `curl https://zyedidia.github.io/eget | bash`
#
# Acknowledgments:
#   - getmic.ro: https://github.com/benweissmann/getmic.ro

set -e -u

githubLatestTag() {
  finalUrl=$(curl "https://github.com/$1/releases/latest" -s -L -I -o /dev/null -w '%{url_effective}')
  printf "%s\n" "${finalUrl##*v}"
}

platform=''
machine=$(uname -m)

if [ "${GETEGET_PLATFORM:-x}" != "x" ]; then
  platform="$GETEGET_PLATFORM"
else
  case "$(uname -s | tr '[:upper:]' '[:lower:]')" in
    "linux")
      case "$machine" in
        "arm64"* | "aarch64"* ) platform='linux_arm64' ;;
        "arm"* | "aarch"*) platform='linux_arm' ;;
        *"86") platform='linux_386' ;;
        *"64") platform='linux_amd64' ;;
      esac
      ;;
    "darwin")
      case "$machine" in
        "arm64"* | "aarch64"* ) platform='darwin_arm64' ;;
        *"64") platform='darwin_amd64' ;;
      esac
      ;;
    "msys"*|"cygwin"*|"mingw"*|*"_nt"*|"win"*)
      case "$machine" in
        *"86") platform='windows_386' ;;
        *"64") platform='windows_amd64' ;;
      esac
      ;;
  esac
fi

if [ "x$platform" = "x" ]; then
  cat << 'EOM'
/=====================================\\
|      COULD NOT DETECT PLATFORM      |
\\=====================================/
Uh oh! We couldn't automatically detect your operating system.
To continue with installation, please choose from one of the following values:
- linux_arm
- linux_arm64
- linux_386
- linux_amd64
- darwin_amd64
- darwin_arm64
- windows_386
- windows_amd64
Export your selection as the GETEGET_PLATFORM environment variable, and then
re-run this script.
For example:
  $ export GETEGET_PLATFORM=linux_amd64
  $ curl https://zyedidia.github.io/eget | bash
EOM
  exit 1
else
  printf "Detected platform: %s\n" "$platform"
fi

TAG=$(githubLatestTag zyedidia/eget)

if [ "x$platform" = "xwindows_amd64" ] || [ "x$platform" = "xwindows_386" ]; then
  extension='zip'
else
  extension='tar.gz'
fi

printf "Latest Version: %s\n" "$TAG"
printf "Downloading https://github.com/zyedidia/eget/releases/download/v%s/eget-%s-%s.%s\n" "$TAG" "$TAG" "$platform" "$extension"

curl -L "https://github.com/zyedidia/eget/releases/download/v$TAG/eget-$TAG-$platform.$extension" > "eget.$extension"

case "$extension" in
  "zip") unzip -j "eget.$extension" -d "eget-$TAG-$platform" ;;
  "tar.gz") tar -xvzf "eget.$extension" "eget-$TAG-$platform/eget" ;;
esac

mv "eget-$TAG-$platform/eget" ./eget

rm "eget.$extension"
rm -rf "eget-$TAG-$platform"

cat <<-'EOM'
Eget has been downloaded to the current directory.
You can run it with:
./eget
EOM
