#!/usr/bin/env bash
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR="${HOME}/.local/share/HydroK"
ICON_DIR="${HOME}/.local/share/icons"
APPLICATIONS_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${APPLICATIONS_DIR}/HydroK.desktop"

if [ ! -d "${SCRIPT_DIR}/dist/HydroK" ]; then
    printf 'Bundle introuvable : %s\n' "${SCRIPT_DIR}/dist/HydroK" >&2
    exit 1
fi
if [ ! -f "${SCRIPT_DIR}/assets/icone_hydrok.png" ]; then
    printf 'Icône introuvable : %s\n' "${SCRIPT_DIR}/assets/icone_hydrok.png" >&2
    exit 1
fi

install -d "${APP_DIR}" "${ICON_DIR}" "${APPLICATIONS_DIR}"
cp -a "${SCRIPT_DIR}/dist/HydroK/." "${APP_DIR}/"
chmod 0755 "${APP_DIR}/HydroK"
install -m 0644 "${SCRIPT_DIR}/assets/icone_hydrok.png" \
    "${ICON_DIR}/hydrok.png"

cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=HydroK
Comment=Mesure et analyse de la conductivité hydraulique
Exec=${APP_DIR}/HydroK
Icon=${ICON_DIR}/hydrok.png
Terminal=false
Categories=Science;
StartupNotify=true
EOF
chmod 0755 "${DESKTOP_FILE}"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "${DESKTOP_FILE}"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APPLICATIONS_DIR}"
fi

printf 'HydroK installé dans %s\n' "${APP_DIR}"
