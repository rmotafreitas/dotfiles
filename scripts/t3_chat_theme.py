#!/usr/bin/env python3
"""Generate the T3 Chat theme files in themes/t3-chat/ from palette.json; --check verifies them."""
import argparse
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / 'themes/t3-chat'
MODES = ('light', 'dark')
VERSION = '1.0.0'
VSIX = THEME / f't3-chat-theme-{VERSION}.vsix'


def oklch_to_hex(css: str) -> str:
    """Convert a CSS oklch() color to sRGB hex, clipping each channel like browsers do."""
    match = re.fullmatch(r'oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)', css)
    if not match:
        raise ValueError(f'Not an oklch() color: {css}')
    lightness, chroma, hue = map(float, match.groups())
    a, b = chroma * math.cos(math.radians(hue)), chroma * math.sin(math.radians(hue))
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    linear = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
              -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
              -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)

    def encode(channel: float) -> int:
        channel = min(max(channel, 0.0), 1.0)
        srgb = 12.92 * channel if channel <= 0.0031308 else 1.055 * channel ** (1 / 2.4) - 0.055
        return round(srgb * 255)

    return '#' + ''.join(f'{encode(c):02x}' for c in linear)


def load_palette() -> dict:
    palette = json.loads((THEME / 'palette.json').read_text())
    for mode in MODES:
        palette[mode]['hex'] = {role: oklch_to_hex(css) for role, css in palette[mode]['roles'].items()}
    return palette


def vscode_theme(mode: str, c: dict, pierre: dict) -> dict:
    """Map T3 Code's theme roles onto VS Code workbench colors; syntax colors come from Pierre."""
    # Pierre's status colors (Git, diff, merge) suit both modes; its surfaces are replaced below.
    colors = {k: v for k, v in pierre['colors'].items()
              if k.startswith(('gitDecoration.', 'diffEditor.', 'merge.', 'editorOverviewRuler.'))
              or k == 'notificationsInfoIcon.foreground'}
    # Pierre uses a key VS Code does not have; this is the registered name.
    colors['diffEditor.removedTextBackground'] = colors.pop('diffEditor.deletedTextBackground')
    selection = c['terminalSelection']
    colors.update({
        'foreground': c['text'],
        'descriptionForeground': c['textMuted'],
        'disabledForeground': c['placeholder'],
        'errorForeground': c['error'],
        'icon.foreground': c['iconMuted'],
        'focusBorder': c['focus'],
        'selection.background': selection,
        'widget.border': c['border'],
        'sash.hoverBorder': c['focus'],
        'textLink.foreground': c['focus'],
        'textLink.activeForeground': c['focus'],
        'textCodeBlock.background': c['codeBackground'],
        'textPreformat.foreground': c['codeForeground'],
        'textPreformat.background': c['codeBackground'],
        'textBlockQuote.background': c['surface'],
        'textBlockQuote.border': c['border'],

        'editor.background': c['canvas'],
        'editor.foreground': c['text'],
        'editorCursor.foreground': c['terminalCursor'],
        'editor.selectionBackground': selection,
        'editor.inactiveSelectionBackground': selection + '99',
        'editor.selectionHighlightBackground': selection + '80',
        'editor.wordHighlightBackground': selection + '66',
        'editor.lineHighlightBackground': c['surface'],
        'editor.lineHighlightBorder': '#00000000',
        'editor.findMatchBackground': c['searchMatchActiveBackground'],
        'editor.findMatchForeground': c['searchMatchActiveForeground'],
        'editor.findMatchHighlightBackground': c['searchMatchBackground'],
        'editor.findMatchHighlightForeground': c['searchMatchForeground'],
        'editorLineNumber.foreground': c['placeholder'],
        'editorLineNumber.activeForeground': c['text'],
        'editorIndentGuide.background1': c['border'],
        'editorIndentGuide.activeBackground1': c['input'],
        'editorWhitespace.foreground': c['border'],
        'editorRuler.foreground': c['border'],
        'editorGutter.background': c['canvas'],
        'editorBracketMatch.background': selection + '80',
        'editorBracketMatch.border': c['focus'],
        'editorError.foreground': c['error'],
        'editorWarning.foreground': c['warning'],
        'editorLink.activeForeground': c['focus'],
        'editorWidget.background': c['surfaceRaised'],
        'editorWidget.foreground': c['text'],
        'editorWidget.border': c['border'],
        'editorHoverWidget.background': c['surfaceOverlay'],
        'editorHoverWidget.border': c['border'],
        'editorSuggestWidget.background': c['surfaceOverlay'],
        'editorSuggestWidget.border': c['border'],
        'editorSuggestWidget.foreground': c['text'],
        'editorSuggestWidget.selectedBackground': c['secondary'],
        'editorSuggestWidget.highlightForeground': c['focus'],
        'peekView.border': c['focus'],
        'peekViewEditor.background': c['surface'],
        'peekViewResult.background': c['surfaceRaised'],
        'peekViewTitle.background': c['surface'],
        'breadcrumb.foreground': c['textMuted'],
        'breadcrumb.focusForeground': c['text'],
        'breadcrumb.background': c['canvas'],

        'titleBar.activeBackground': c['chrome'],
        'titleBar.activeForeground': c['toolbarForeground'],
        'titleBar.inactiveBackground': c['chrome'],
        'titleBar.inactiveForeground': c['placeholder'],
        'titleBar.border': c['toolbarBorder'],
        'activityBar.background': c['sidebar'],
        'activityBar.foreground': c['sidebarForeground'],
        'activityBar.inactiveForeground': c['sidebarMutedForeground'],
        'activityBar.border': c['sidebarBorder'],
        'activityBar.activeBorder': c['focus'],
        'activityBarBadge.background': c['accent'],
        'activityBarBadge.foreground': c['accentForeground'],
        'sideBar.background': c['sidebar'],
        'sideBar.foreground': c['sidebarForeground'],
        'sideBar.border': c['sidebarBorder'],
        'sideBarTitle.foreground': c['sidebarForeground'],
        'sideBarSectionHeader.background': c['sidebar'],
        'sideBarSectionHeader.foreground': c['sidebarMutedForeground'],
        'sideBarSectionHeader.border': c['sidebarBorder'],
        # Selections must show on the sidebar and on white/near-black pickers alike.
        'list.activeSelectionBackground': c['secondary'],
        'list.activeSelectionForeground': c['text'],
        'list.inactiveSelectionBackground': c['secondary'] + 'b3',
        'list.hoverBackground': c['secondary'] + '80',
        'list.focusOutline': c['focus'],
        'list.highlightForeground': c['focus'],
        'tab.activeBackground': c['canvas'],
        'tab.activeForeground': c['text'],
        'tab.activeBorderTop': c['focus'],
        'tab.inactiveBackground': c['toolbar'],
        'tab.inactiveForeground': c['placeholder'],
        'tab.hoverBackground': c['toolbarControl'],
        'tab.border': c['toolbarBorder'],
        'editorGroupHeader.tabsBackground': c['toolbar'],
        'editorGroupHeader.tabsBorder': c['toolbarBorder'],
        'editorGroup.border': c['border'],
        'panel.background': c['terminalBackground'],
        'panel.border': c['border'],
        'panelTitle.activeBorder': c['focus'],
        'panelTitle.activeForeground': c['text'],
        'panelTitle.inactiveForeground': c['placeholder'],
        'statusBar.background': c['chrome'],
        'statusBar.foreground': c['toolbarForeground'],
        'statusBar.border': c['toolbarBorder'],
        'statusBar.noFolderBackground': c['chrome'],
        'statusBar.debuggingBackground': c['warning'],
        'statusBar.debuggingForeground': c['searchMatchActiveForeground'],
        'statusBarItem.hoverBackground': c['toolbarControlHover'],
        'statusBarItem.remoteBackground': c['accent'],
        'statusBarItem.remoteForeground': c['accentForeground'],

        'input.background': c['surfaceOverlay'],
        'input.border': c['input'],
        'input.foreground': c['text'],
        'input.placeholderForeground': c['placeholder'],
        'inputOption.activeBorder': c['focus'],
        'dropdown.background': c['surfaceOverlay'],
        'dropdown.border': c['input'],
        'dropdown.foreground': c['text'],
        'button.background': c['messageAction'],
        'button.foreground': c['messageActionForeground'],
        'button.hoverBackground': c['messageActionHover'],
        'button.secondaryBackground': c['secondary'],
        'button.secondaryForeground': c['secondaryForeground'],
        'button.secondaryHoverBackground': c['toolbarControlHover'],
        'badge.background': c['accent'],
        'badge.foreground': c['accentForeground'],
        'progressBar.background': c['focus'],
        'quickInput.background': c['surfaceOverlay'],
        'quickInput.foreground': c['text'],
        'quickInputTitle.background': c['surface'],
        'quickInputList.focusBackground': c['secondary'],
        'menu.background': c['surfaceOverlay'],
        'menu.foreground': c['text'],
        'menu.selectionBackground': c['secondary'],
        'menu.selectionForeground': c['text'],
        'menu.border': c['border'],
        'menu.separatorBackground': c['border'],
        'notifications.background': c['surfaceRaised'],
        'notifications.foreground': c['text'],
        'notifications.border': c['border'],
        'notificationCenterHeader.background': c['surface'],
        'notificationLink.foreground': c['focus'],
        'notificationsErrorIcon.foreground': c['error'],
        'notificationsWarningIcon.foreground': c['warning'],
        'scrollbarSlider.background': c['terminalScrollbar'] + '99',
        'scrollbarSlider.hoverBackground': c['terminalScrollbarHover'] + 'b3',
        'scrollbarSlider.activeBackground': c['focus'] + '80',

        # No terminal.ansi* colors: VS Code's defaults are what T3 Code's terminal uses.
        'terminal.background': c['terminalBackground'],
        'terminal.foreground': c['terminalForeground'],
        'terminalCursor.foreground': c['terminalCursor'],
        'terminal.selectionBackground': selection,
        'terminal.border': c['border'],
    })
    return {
        '$schema': 'vscode://schemas/color-theme',
        'name': f'T3 Chat {mode.title()}',
        'type': mode,
        'semanticHighlighting': True,
        'colors': colors,
        'tokenColors': pierre['tokenColors'],
        'semanticTokenColors': pierre['semanticTokenColors'],
    }


def ghostty_theme(c: dict, ansi: list) -> str:
    lines = [f'background = {c["terminalBackground"]}', f'foreground = {c["terminalForeground"]}',
             f'cursor-color = {c["terminalCursor"]}', f'cursor-text = {c["terminalBackground"]}',
             f'selection-background = {c["terminalSelection"]}', f'selection-foreground = {c["terminalForeground"]}']
    lines += [f'palette = {i}={color}' for i, color in enumerate(ansi)]
    return '\n'.join(lines) + '\n'


def xfce_theme(mode: str, c: dict, ansi: list) -> str:
    return '\n'.join([
        '[Scheme]', f'Name=T3 Chat {mode.title()}',
        f'ColorForeground={c["terminalForeground"]}', f'ColorBackground={c["terminalBackground"]}',
        'ColorCursorUseDefault=FALSE', f'ColorCursor={c["terminalCursor"]}', f'ColorCursorForeground={c["terminalBackground"]}',
        'ColorSelectionUseDefault=FALSE', f'ColorSelection={c["terminalForeground"]}',
        f'ColorSelectionBackground={c["terminalSelection"]}',
        'ColorBoldUseDefault=TRUE', f'TabActivityColor={c["focus"]}',
        'ColorPalette=' + ';'.join(ansi)]) + '\n'


def btop_theme(c: dict) -> str:
    accent = (c['placeholder'], c['focus'], c['error'])
    calm = (c['secondaryForeground'], c['textMuted'], c['focus'])
    heat = (c['warningForeground'], c['warning'], c['error'])
    colors = {
        'main_bg': c['canvas'], 'main_fg': c['text'], 'title': c['text'], 'hi_fg': c['focus'],
        'selected_bg': c['secondary'], 'selected_fg': c['text'], 'inactive_fg': c['placeholder'],
        'graph_text': c['textMuted'], 'meter_bg': c['border'], 'proc_misc': c['focus'],
        'cpu_box': c['muted'], 'mem_box': c['muted'], 'net_box': c['muted'],
        'proc_box': c['muted'], 'div_line': c['border'],
    }
    for name, gradient in (('temp', heat), ('cpu', accent), ('free', calm), ('cached', calm),
                           ('available', calm), ('used', accent), ('download', accent),
                           ('upload', calm), ('process', accent)):
        colors.update({f'{name}_{step}': color for step, color in zip(('start', 'mid', 'end'), gradient)})
    return '# T3 Chat for btop, generated by scripts/t3_chat_theme.py\n' + ''.join(
        f'theme[{key}]="{value}"\n' for key, value in colors.items())


def package_json() -> dict:
    return {
        'name': 't3-chat-theme',
        'displayName': 'T3 Chat Theme',
        'description': "T3 Code's T3 Chat palette in light and dark, with Pierre syntax colors",
        'version': VERSION,
        'publisher': 'rmotafreitas',
        'license': 'SEE LICENSE IN LICENSE.txt',
        'repository': {'type': 'git', 'url': 'https://github.com/rmotafreitas/dotfiles.git'},
        'engines': {'vscode': '^1.70.0'},
        'categories': ['Themes'],
        'keywords': ['theme', 'color-theme', 't3', 't3-chat', 'pink'],
        'contributes': {'themes': [
            {'label': 'T3 Chat Light', 'uiTheme': 'vs', 'path': './themes/t3-chat-light-color-theme.json'},
            {'label': 'T3 Chat Dark', 'uiTheme': 'vs-dark', 'path': './themes/t3-chat-dark-color-theme.json'},
        ]},
    }


def vsix(files: dict) -> bytes:
    """Package the extension like `vsce package` does; fixed timestamps keep it reproducible."""
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="t3-chat-theme" Version="{VERSION}" Publisher="rmotafreitas" />
    <DisplayName>T3 Chat Theme</DisplayName>
    <Description xml:space="preserve">{package_json()['description'].replace("'", '&apos;')}</Description>
    <Tags>theme,color-theme,t3,t3-chat,pink</Tags>
    <Categories>Themes</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.70.0" />
      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="https://github.com/rmotafreitas/dotfiles.git" />
    </Properties>
    <License>extension/LICENSE.txt</License>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" Addressable="true" />
  </Assets>
</PackageManifest>
'''
    content_types = ('<?xml version="1.0" encoding="utf-8"?>\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension=".json" ContentType="application/json" />'
                     '<Default Extension=".md" ContentType="text/markdown" />'
                     '<Default Extension=".txt" ContentType="text/plain" />'
                     '<Default Extension=".vsixmanifest" ContentType="text/xml" /></Types>\n')
    entries = {'[Content_Types].xml': content_types, 'extension.vsixmanifest': manifest,
               **{f'extension/{name}': data for name, data in files.items()}}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def outputs() -> dict:
    """Every generated file: path relative to themes/t3-chat -> contents."""
    palette = load_palette()
    license_text = (THEME / 'vscode/LICENSE.txt').read_text()
    readme = (THEME / 'vscode/README.md').read_text()
    out = {'vscode/package.json': json.dumps(package_json(), indent=2) + '\n'}
    for mode in MODES:
        c, ansi = palette[mode]['hex'], palette[mode]['ansi']
        pierre = json.loads((THEME / f'pierre/pierre-{mode}.json').read_text())
        title = mode.title()
        out[f'vscode/themes/t3-chat-{mode}-color-theme.json'] = json.dumps(vscode_theme(mode, c, pierre), indent=2) + '\n'
        out[f'ghostty/T3 Chat {title}'] = ghostty_theme(c, ansi)
        out[f'xfce4-terminal/t3-chat-{mode}.theme'] = xfce_theme(mode, c, ansi)
        out[f'btop/t3-chat-{mode}.theme'] = btop_theme(c)
    extension = {name.removeprefix('vscode/'): data for name, data in out.items() if name.startswith('vscode/')}
    extension.update({'README.md': readme, 'LICENSE.txt': license_text})
    out[VSIX.name] = vsix(extension)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if a generated file is missing or outdated')
    args = parser.parse_args()
    stale = []
    for name, data in outputs().items():
        path = THEME / name
        data = data.encode() if isinstance(data, str) else data
        if path.exists() and path.read_bytes() == data:
            continue
        if args.check:
            stale.append(name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f'Wrote themes/t3-chat/{name}')
    if stale:
        print('Outdated; run python3 scripts/t3_chat_theme.py:', *stale, sep='\n  ', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
