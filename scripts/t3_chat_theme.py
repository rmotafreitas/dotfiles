#!/usr/bin/env python3
"""Generate the T3 Chat theme files in themes/t3-chat/ from palette.json; --check verifies them."""
import argparse
import io
import json
import math
from pathlib import Path
import plistlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / 'themes/t3-chat'
MODES = ('light', 'dark')
VERSION = '1.0.0'
VSIX = THEME / f't3-chat-theme-{VERSION}.vsix'
JETBRAINS_PLUGIN = THEME / f'jetbrains/t3-chat-theme-{VERSION}.jar'


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
    return zip_bytes({'[Content_Types].xml': content_types, 'extension.vsixmanifest': manifest,
                      **{f'extension/{name}': data for name, data in files.items()}})


def zip_bytes(entries: dict) -> bytes:
    """A zip archive with fixed timestamps, so regenerating it gives identical bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def blend(color: str, over: str, amount: float) -> str:
    """`color` at `amount` opacity over `over`, for formats without alpha."""
    a, b = bytes.fromhex(color[1:7]), bytes.fromhex(over[1:7])
    return '#' + ''.join(f'{round(x * amount + y * (1 - amount)):02x}' for x, y in zip(a, b))


def syntax_colors(pierre: dict) -> dict:
    """Pierre's color for each syntax category, for editors that have no TextMate scopes."""
    semantic = pierre['semanticTokenColors']

    def scope(name: str) -> str:
        for rule in pierre['tokenColors']:
            scopes = rule.get('scope', [])
            if name in ([scopes] if isinstance(scopes, str) else scopes) and 'foreground' in rule['settings']:
                return rule['settings']['foreground']
        raise KeyError(name)

    git = pierre['colors']
    return {
        'comment': semantic['comment'], 'string': semantic['string'], 'number': semantic['number'],
        'regexp': semantic['regexp'], 'keyword': semantic['keyword'], 'function': semantic['function'],
        'type': semantic['type'], 'namespace': semantic['namespace'], 'variable': semantic['variable'],
        'parameter': semantic['parameter'], 'property': semantic['property'], 'constant': semantic['variable.constant'],
        'builtin': semantic['variable.defaultLibrary'], 'decorator': semantic['decorator'],
        'operator': scope('keyword.operator'), 'punctuation': scope('punctuation'), 'tag': scope('entity.name.tag'),
        'attribute': scope('entity.other.attribute-name'), 'escape': scope('constant.character.escape'),
        'heading': scope('markup.heading'), 'literal': scope('constant.language'),
        'added': git['gitDecoration.addedResourceForeground'], 'modified': git['gitDecoration.modifiedResourceForeground'],
        'deleted': git['gitDecoration.deletedResourceForeground'],
    }


ANSI_NAMES = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')


def jetbrains_scheme(mode: str, c: dict, s: dict, ansi: list) -> str:
    """Editor color scheme (.icls); attributes not set here come from Darcula or the light Default."""
    root = ET.Element('scheme', name=f'T3 Chat {mode.title()}', version='142',
                      parent_scheme='Darcula' if mode == 'dark' else 'Default')
    colors = ET.SubElement(root, 'colors')
    for key, value in {
        'CARET_COLOR': c['terminalCursor'], 'CARET_ROW_COLOR': c['surface'],
        'SELECTION_BACKGROUND': c['terminalSelection'], 'LINE_NUMBERS_COLOR': c['placeholder'],
        'LINE_NUMBER_ON_CARET_ROW_COLOR': c['text'], 'GUTTER_BACKGROUND': c['canvas'],
        'INDENT_GUIDE': c['border'], 'SELECTED_INDENT_GUIDE': c['input'], 'VISUAL_INDENT_GUIDE': c['border'],
        'WHITESPACES': c['border'], 'RIGHT_MARGIN_COLOR': c['border'], 'TEARLINE_COLOR': c['border'],
        'SELECTED_TEARLINE_COLOR': c['focus'], 'METHOD_SEPARATORS_COLOR': c['border'],
        'CONSOLE_BACKGROUND_KEY': c['terminalBackground'], 'DOCUMENTATION_COLOR': c['surfaceRaised'],
        'LOOKUP_COLOR': c['surfaceOverlay'], 'NOTIFICATION_BACKGROUND': c['surfaceRaised'],
        'PREVIEW_BACKGROUND': c['surface'], 'ADDED_LINES_COLOR': s['added'], 'MODIFIED_LINES_COLOR': s['modified'],
        'DELETED_LINES_COLOR': s['deleted'], 'FILESTATUS_ADDED': s['added'], 'FILESTATUS_MODIFIED': s['modified'],
        'FILESTATUS_DELETED': s['deleted'],
    }.items():
        ET.SubElement(colors, 'option', name=key, value=value[1:7])
    attributes = ET.SubElement(root, 'attributes')

    def attr(key, fg=None, bg=None, font=0, effect=None, effect_type=None, stripe=None):
        value = ET.SubElement(ET.SubElement(attributes, 'option', name=key), 'value')
        for name, color in (('FOREGROUND', fg), ('BACKGROUND', bg)):
            if color:
                ET.SubElement(value, 'option', name=name, value=color[1:7])
        if font:  # 1 bold, 2 italic
            ET.SubElement(value, 'option', name='FONT_TYPE', value=str(font))
        if effect:  # 1 underline, 2 wave, 3 strikeout
            ET.SubElement(value, 'option', name='EFFECT_COLOR', value=effect[1:7])
            ET.SubElement(value, 'option', name='EFFECT_TYPE', value=str(effect_type))
        if stripe:
            ET.SubElement(value, 'option', name='ERROR_STRIPE_COLOR', value=stripe[1:7])

    attr('TEXT', c['text'], c['canvas'])
    for key, category in {
        'DEFAULT_KEYWORD': 'keyword', 'DEFAULT_STRING': 'string', 'DEFAULT_NUMBER': 'number',
        'DEFAULT_LINE_COMMENT': 'comment', 'DEFAULT_BLOCK_COMMENT': 'comment', 'DEFAULT_DOC_COMMENT': 'comment',
        'DEFAULT_DOC_MARKUP': 'comment', 'DEFAULT_DOC_COMMENT_TAG': 'keyword',
        'DEFAULT_FUNCTION_DECLARATION': 'function', 'DEFAULT_FUNCTION_CALL': 'function',
        'DEFAULT_INSTANCE_METHOD': 'function', 'DEFAULT_STATIC_METHOD': 'function',
        'DEFAULT_CLASS_NAME': 'type', 'DEFAULT_CLASS_REFERENCE': 'type', 'DEFAULT_INTERFACE_NAME': 'type',
        'DEFAULT_CONSTANT': 'constant', 'DEFAULT_GLOBAL_VARIABLE': 'variable', 'DEFAULT_PARAMETER': 'parameter',
        'DEFAULT_INSTANCE_FIELD': 'property', 'DEFAULT_STATIC_FIELD': 'property', 'DEFAULT_METADATA': 'decorator',
        'DEFAULT_OPERATION_SIGN': 'operator', 'DEFAULT_BRACES': 'punctuation', 'DEFAULT_BRACKETS': 'punctuation',
        'DEFAULT_PARENTHS': 'punctuation', 'DEFAULT_COMMA': 'punctuation', 'DEFAULT_DOT': 'punctuation',
        'DEFAULT_SEMICOLON': 'punctuation', 'DEFAULT_VALID_STRING_ESCAPE': 'escape', 'DEFAULT_TAG': 'tag',
        'DEFAULT_ATTRIBUTE': 'attribute', 'DEFAULT_ENTITY': 'escape', 'DEFAULT_LABEL': 'namespace',
        'DEFAULT_PREDEFINED_SYMBOL': 'builtin',
    }.items():
        attr(key, s[category])
    for key in ('DEFAULT_IDENTIFIER', 'DEFAULT_LOCAL_VARIABLE'):
        attr(key, c['text'])
    attr('DEFAULT_INVALID_STRING_ESCAPE', c['error'], effect=c['error'], effect_type=2)
    attr('ERRORS_ATTRIBUTES', effect=c['error'], effect_type=2, stripe=c['error'])
    attr('WARNING_ATTRIBUTES', effect=c['warning'], effect_type=2, stripe=c['warning'])
    attr('WRONG_REFERENCES_ATTRIBUTES', c['error'])
    attr('DEPRECATED_ATTRIBUTES', effect=c['textMuted'], effect_type=3)
    attr('NOT_USED_ELEMENT_ATTRIBUTES', c['placeholder'], stripe=c['warning'])
    attr('SEARCH_RESULT_ATTRIBUTES', c['searchMatchForeground'], c['searchMatchBackground'], stripe=c['searchMatchActiveBackground'])
    attr('TEXT_SEARCH_RESULT_ATTRIBUTES', c['searchMatchForeground'], c['searchMatchBackground'], stripe=c['searchMatchActiveBackground'])
    attr('WRITE_SEARCH_RESULT_ATTRIBUTES', c['searchMatchActiveForeground'], c['searchMatchActiveBackground'])
    attr('IDENTIFIER_UNDER_CARET_ATTRIBUTES', bg=blend(c['terminalSelection'], c['canvas'], 0.6), stripe=c['focus'])
    attr('WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES', bg=c['terminalSelection'], stripe=c['focus'])
    attr('MATCHED_BRACE_ATTRIBUTES', c['focus'], blend(c['terminalSelection'], c['canvas'], 0.6), font=1)
    attr('UNMATCHED_BRACE_ATTRIBUTES', c['error'], c['errorSurface'])
    attr('HYPERLINK_ATTRIBUTES', c['focus'], effect=c['focus'], effect_type=1)
    attr('FOLDED_TEXT_ATTRIBUTES', c['textMuted'], c['surface'])
    attr('INLAY_DEFAULT', c['placeholder'], c['surface'])
    attr('TODO_DEFAULT_ATTRIBUTES', c['focus'], font=2, stripe=c['focus'])
    for key, color in (('DIFF_INSERTED', s['added']), ('DIFF_MODIFIED', s['modified']), ('DIFF_DELETED', s['deleted'])):
        attr(key, bg=blend(color, c['canvas'], 0.2), stripe=color)
    attr('CONSOLE_NORMAL_OUTPUT', c['terminalForeground'])
    attr('CONSOLE_ERROR_OUTPUT', c['error'])
    attr('CONSOLE_USER_INPUT', s['string'])
    attr('CONSOLE_SYSTEM_OUTPUT', c['textMuted'])
    console = ('BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'GRAY', 'DARKGRAY', 'RED_BRIGHT',
               'GREEN_BRIGHT', 'YELLOW_BRIGHT', 'BLUE_BRIGHT', 'MAGENTA_BRIGHT', 'CYAN_BRIGHT', 'WHITE')
    for name, color in zip(console, ansi):
        attr(f'CONSOLE_{name}_OUTPUT', color)
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='unicode') + '\n'


def jetbrains_ui_theme(mode: str, c: dict) -> dict:
    """IDE theme on top of JetBrains' own new UI theme, which supplies everything not set here."""
    selection, canvas = c['secondary'], c['canvas']
    return {
        'name': f'T3 Chat {mode.title()}',
        'dark': mode == 'dark',
        'author': 'rmotafreitas',
        'parentTheme': 'ExperimentalDark' if mode == 'dark' else 'ExperimentalLight',
        'editorScheme': f'/themes/t3-chat-{mode}.xml',
        'ui': {
            '*': {
                'background': canvas, 'foreground': c['text'], 'infoForeground': c['textMuted'],
                'selectionBackground': selection, 'selectionForeground': c['text'],
                'selectionInactiveBackground': blend(selection, canvas, 0.7),
                'hoverBackground': blend(selection, canvas, 0.5), 'disabledForeground': c['placeholder'],
                'inactiveForeground': c['placeholder'], 'borderColor': c['border'], 'separatorColor': c['border'],
                'focusColor': c['focus'], 'acceleratorForeground': c['textMuted'],
            },
            'MainWindow': {'background': c['chrome']},
            'MainToolbar': {'background': c['chrome'], 'foreground': c['toolbarForeground'],
                            'Icon': {'hoverBackground': c['toolbarControlHover']},
                            'Dropdown': {'hoverBackground': c['toolbarControlHover']}},
            'ToolWindow': {'background': c['sidebar'],
                           'Header': {'background': c['sidebar'], 'inactiveBackground': c['sidebar']},
                           'Stripe': {'background': c['sidebar']},
                           'Button': {'selectedBackground': selection, 'hoverBackground': c['toolbarControlHover']}},
            'Tree': {'background': c['sidebar'], 'foreground': c['sidebarForeground']},
            'EditorTabs': {'background': c['toolbar'], 'underlinedTabBackground': canvas, 'underlineColor': c['focus'],
                           'inactiveUnderlineColor': c['muted'], 'hoverBackground': c['toolbarControl'],
                           'underlinedTabForeground': c['text']},
            'StatusBar': {'background': c['chrome'], 'borderColor': c['toolbarBorder'],
                          'Widget': {'hoverBackground': c['toolbarControlHover']}},
            'Table': {'stripeColor': c['surface']},
            'Button': {'startBackground': c['surfaceOverlay'], 'endBackground': c['surfaceOverlay'],
                       'startBorderColor': c['input'], 'endBorderColor': c['input'], 'foreground': c['text'],
                       'default': {'startBackground': c['messageAction'], 'endBackground': c['messageAction'],
                                   'startBorderColor': c['messageAction'], 'endBorderColor': c['messageAction'],
                                   'foreground': c['messageActionForeground'], 'focusColor': c['focus']}},
            'Link': {'activeForeground': c['focus'], 'hoverForeground': c['focus'], 'pressedForeground': c['focus'],
                     'visitedForeground': c['focus']},
            'Component': {'focusColor': c['focus'], 'focusedBorderColor': c['focus'], 'borderColor': c['input']},
            'TextField': {'background': c['surfaceOverlay']},
            'ComboBox': {'background': c['surfaceOverlay']},
            'TextArea': {'background': c['surfaceOverlay']},
            'Popup': {'background': c['surfaceOverlay'], 'borderColor': c['border'],
                      'Header': {'activeBackground': c['surface']}},
            'PopupMenu': {'background': c['surfaceOverlay']},
            'MenuItem': {'selectionBackground': selection},
            'ProgressBar': {'progressColor': c['focus'], 'indeterminateStartColor': c['focus'],
                            'indeterminateEndColor': c['accent'], 'trackColor': c['border']},
            'Notification': {'background': c['surfaceRaised'], 'borderColor': c['border']},
            'Counter': {'background': c['accent'], 'foreground': c['accentForeground']},
            'ActionButton': {'hoverBackground': c['toolbarControlHover'], 'pressedBackground': selection},
            'ToolTip': {'background': c['surfaceOverlay'], 'foreground': c['text']},
            'Editor': {'background': canvas, 'foreground': c['text']},
        },
    }


def jetbrains_plugin(files: dict) -> bytes:
    """An IDE plugin (.jar) with both themes; install it with Plugins → Install Plugin from Disk."""
    plugin_xml = f'''<idea-plugin>
  <id>dev.rmotafreitas.t3-chat-theme</id>
  <name>T3 Chat Theme</name>
  <version>{VERSION}</version>
  <vendor url="https://github.com/rmotafreitas/dotfiles">rmotafreitas</vendor>
  <description><![CDATA[T3 Code's T3 Chat palette in light and dark for JetBrains IDEs, with Pierre syntax colors.]]></description>
  <idea-version since-build="231"/>
  <depends>com.intellij.modules.platform</depends>
  <extensions defaultExtensionNs="com.intellij">
    <themeProvider id="t3-chat-light" path="/themes/t3-chat-light.theme.json"/>
    <themeProvider id="t3-chat-dark" path="/themes/t3-chat-dark.theme.json"/>
  </extensions>
</idea-plugin>
'''
    return zip_bytes({'META-INF/plugin.xml': plugin_xml, **files})


def xcode_theme(c: dict, s: dict) -> bytes:
    """Xcode .xccolortheme (a property list of "r g b a" color strings)."""
    def rgba(color: str) -> str:
        return ' '.join(f'{x / 255:.6f}' for x in bytes.fromhex(color[1:7])) + ' 1'

    font = 'SFMono-Regular - 13.0'
    syntax = {
        'attribute': 'decorator', 'character': 'string', 'comment': 'comment', 'comment.doc': 'comment',
        'comment.doc.keyword': 'keyword', 'declaration.other': 'function', 'declaration.type': 'type',
        'identifier.class': 'type', 'identifier.class.system': 'type', 'identifier.constant': 'constant',
        'identifier.constant.system': 'constant', 'identifier.function': 'function',
        'identifier.function.system': 'function', 'identifier.macro': 'namespace',
        'identifier.macro.system': 'namespace', 'identifier.type': 'type', 'identifier.type.system': 'type',
        'identifier.variable': 'property', 'identifier.variable.system': 'builtin', 'keyword': 'keyword',
        'number': 'number', 'preprocessor': 'namespace', 'string': 'string', 'regex': 'regexp',
        'regex.capturename': 'regexp', 'regex.charname': 'regexp', 'regex.number': 'number', 'regex.other': 'regexp',
    }
    colors = {f'xcode.syntax.{key}': rgba(s[category]) for key, category in syntax.items()}
    colors.update({'xcode.syntax.plain': rgba(c['text']), 'xcode.syntax.mark': rgba(c['textMuted']),
                   'xcode.syntax.markup.code': rgba(c['codeForeground']), 'xcode.syntax.url': rgba(c['focus'])})
    theme = {
        'DVTFontAndColorVersion': 1, 'DVTFontSizeModifier': 0, 'DVTLineSpacing': 1.1,
        'DVTSourceTextBackground': rgba(c['canvas']), 'DVTSourceTextBlockDimBackgroundColor': rgba(c['surface']),
        'DVTSourceTextCurrentLineHighlightColor': rgba(c['surface']),
        'DVTSourceTextInsertionPointColor': rgba(c['terminalCursor']),
        'DVTSourceTextInvisiblesColor': rgba(c['border']), 'DVTSourceTextSelectionColor': rgba(c['terminalSelection']),
        'DVTSourceTextSyntaxColors': colors, 'DVTSourceTextSyntaxFonts': {key: font for key in colors},
        'DVTConsoleTextBackgroundColor': rgba(c['terminalBackground']),
        'DVTConsoleTextInsertionPointColor': rgba(c['terminalCursor']),
        'DVTConsoleTextSelectionColor': rgba(c['terminalSelection']),
        'DVTDebuggerInstructionPointerColor': rgba(c['focus']),
        'DVTMarkupTextBackgroundColor': rgba(c['surface']), 'DVTMarkupTextBorderColor': rgba(c['border']),
        'DVTMarkupTextEmphasisColor': rgba(c['text']), 'DVTMarkupTextInlineCodeColor': rgba(c['codeForeground']),
        'DVTMarkupTextLinkColor': rgba(c['focus']), 'DVTMarkupTextNormalColor': rgba(c['text']),
        'DVTMarkupTextOtherHeadingColor': rgba(c['text']), 'DVTMarkupTextPrimaryHeadingColor': rgba(c['text']),
        'DVTMarkupTextSecondaryHeadingColor': rgba(c['text']), 'DVTMarkupTextStrongColor': rgba(c['text']),
        'DVTScrollbarMarkerAnalyzerColor': rgba(c['focus']), 'DVTScrollbarMarkerBreakpointColor': rgba(c['focus']),
        'DVTScrollbarMarkerDiffColor': rgba(s['modified']), 'DVTScrollbarMarkerDiffConflictColor': rgba(c['error']),
        'DVTScrollbarMarkerErrorColor': rgba(c['error']), 'DVTScrollbarMarkerRuntimeIssueColor': rgba(c['accent']),
        'DVTScrollbarMarkerWarningColor': rgba(c['warning']),
    }
    for name, color in (('DebuggerInput', s['string']), ('DebuggerOutput', c['text']), ('DebuggerPrompt', c['focus']),
                        ('ExectuableInput', s['string']), ('ExectuableOutput', c['text'])):
        theme[f'DVTConsole{name}TextColor'] = rgba(color)
        theme[f'DVTConsole{name}TextFont'] = font
    for name in ('Code', 'Emphasis', 'Link', 'Normal', 'OtherHeading', 'PrimaryHeading', 'SecondaryHeading', 'Strong'):
        theme[f'DVTMarkupText{name}Font'] = font
    return plistlib.dumps(dict(sorted(theme.items())))


def windows_terminal(palette: dict) -> str:
    """A Windows Terminal fragment with both color schemes."""
    order = ('black', 'red', 'green', 'yellow', 'blue', 'purple', 'cyan', 'white')
    schemes = []
    for mode in MODES:
        c, ansi = palette[mode]['hex'], palette[mode]['ansi']
        scheme = {'name': f'T3 Chat {mode.title()}', 'background': c['terminalBackground'],
                  'foreground': c['terminalForeground'], 'cursorColor': c['terminalCursor'],
                  'selectionBackground': c['terminalSelection']}
        scheme.update({name: ansi[i] for i, name in enumerate(order)})
        scheme.update({'bright' + name.title(): ansi[i + 8] for i, name in enumerate(order)})
        schemes.append(scheme)
    return json.dumps({'schemes': schemes}, indent=2) + '\n'


# Notepad++ style names, matched in order; the first word found decides the color.
NOTEPAD_CATEGORIES = (
    (('ERROR', 'ILLEGAL', 'GARBAGE', 'BAD ', 'WRONG', 'UNKNOWN'), 'error'),
    (('COMMENT', 'DOC COMMENT'), 'comment'),
    (('REGEX',), 'regexp'),
    (('ESCAPE',), 'escape'),
    (('STRING', 'CHAR', 'HEREDOC', 'BACKTICK', 'QUOTE', 'VERBATIM', 'TRIPLE', 'LITERAL'), 'string'),
    (('NUMBER', 'NUMERIC', 'HEX', 'BINARY', 'INTEGER', 'FLOAT', 'DIGIT', 'DATE', 'TIME'), 'number'),
    (('ADDED', 'ADDITION', 'INSERTED'), 'added'),
    (('DELETED', 'DELETION', 'REMOVED'), 'deleted'),
    (('CHANGED', 'MODIFIED'), 'modified'),
    (('PREPROCESSOR', 'DIRECTIVE', 'PRAGMA', 'IFDEF', 'MACRO', 'IMPORT', 'INCLUDE'), 'namespace'),
    (('DECORATOR', 'ANNOTATION'), 'decorator'),
    (('TYPE', 'CLASS', 'STRUCT', 'INTERFACE'), 'type'),
    (('FUNC', 'METHOD', 'CMDLET', 'CALLABLE', 'COMMAND', 'BUILTIN', 'BUILT-IN'), 'function'),
    (('TAG', 'ELEMENT'), 'tag'),
    (('ATTRIBUTE', 'PROPERTY', 'PROPERTIES', 'KEY', 'PARAM'), 'attribute'),
    (('VARIABLE', ' VAR', 'IDENTIFIER'), 'variable'),
    (('CONSTANT', 'BOOL', 'NULL'), 'constant'),
    (('OPERATOR', 'DELIMITER', 'PUNCT', 'BRACE', 'BRACKET', 'ASSIGN'), 'operator'),
    (('INSTRUCTION', 'KEYWORD', 'WORD', 'RESERVED', 'STATEMENT', 'LABEL'), 'keyword'),
    (('H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HEADER', 'HEADING', 'SECTION'), 'heading'),
)


def notepad_theme(c: dict, s: dict, ansi: list, model: str) -> str:
    """Recolor Notepad++'s style model; style IDs, fonts and keywords stay as Notepad++ defines them."""
    root = ET.fromstring(model)
    colors = {**s, 'error': c['error'], 'text': c['text']}

    def hexcode(color: str) -> str:
        return color[1:7].upper()

    # "ANSI COLOR <name>" styles use the classic 16-color names (brown is 3, yellow is 11).
    classic = ('BLACK', 'RED', 'GREEN', 'BROWN', 'BLUE', 'MAGENTA', 'CYAN', 'GRAY', 'DARK GRAY', 'BRIGHT RED',
               'BRIGHT GREEN', 'YELLOW', 'BRIGHT BLUE', 'BRIGHT MAGENTA', 'BRIGHT CYAN', 'WHITE')
    for lexer in root.find('LexerStyles'):
        for style in lexer:
            name = style.get('name', '').upper()
            fg, bg = c['text'], c['canvas']
            combo = re.fullmatch(r'(BOLD )?(\w+) ON (\w+)', name)
            ansi_name = re.fullmatch(r'ANSI COLOR (.+)', name)
            if combo:  # ANSI escape previews such as "BOLD RED on BLACK"; bold uses the bright color
                bold, fg_name, bg_name = combo.groups()
                if fg_name.lower() in ANSI_NAMES:
                    fg = ansi[ANSI_NAMES.index(fg_name.lower()) + (8 if bold else 0)]
                if bg_name.lower() in ANSI_NAMES:
                    bg = ansi[ANSI_NAMES.index(bg_name.lower())]
            elif ansi_name and ansi_name.group(1) in classic:
                fg = ansi[classic.index(ansi_name.group(1))]
            else:
                for words, category in NOTEPAD_CATEGORIES:
                    if any(word in name for word in words):
                        fg = colors[category]
                        break
            style.set('fgColor', hexcode(fg))
            style.set('bgColor', hexcode(bg))
    globals_ = {
        'Default Style': (c['text'], c['canvas']), 'Global override': (c['text'], c['canvas']),
        'Indent guideline style': (c['border'], c['canvas']), 'Brace highlight style': (c['focus'], c['terminalSelection']),
        'Bad brace colour': (c['error'], c['errorSurface']), 'Current line background colour': (c['text'], c['surface']),
        'Selected text colour': (c['text'], c['terminalSelection']), 'Multi-selected text color': (c['text'], c['terminalSelection']),
        'Caret colour': (c['terminalCursor'], c['canvas']), 'Multi-edit carets color': (c['focus'], c['canvas']),
        'Edge colour': (c['border'], c['canvas']), 'Line number margin': (c['placeholder'], c['canvas']),
        'Bookmark margin': (c['placeholder'], c['canvas']), 'Fold': (c['placeholder'], c['canvas']),
        'Fold active': (c['focus'], c['canvas']), 'Fold margin': (c['canvas'], c['canvas']),
        'White space symbol': (c['border'], c['canvas']), 'Smart Highlighting': (c['text'], c['secondary']),
        'Find Mark Style': (c['searchMatchForeground'], c['searchMatchBackground']),
        'Incremental highlight all': (c['searchMatchActiveForeground'], c['searchMatchActiveBackground']),
        'Tags match highlighting': (c['text'], c['secondary']), 'Tags attribute': (c['text'], c['accentSurface']),
        'Find status: Not found': (c['error'], c['canvas']), 'Find status: Message': (c['focus'], c['canvas']),
        'Find status: Search end reached': (c['warningForeground'], c['canvas']),
        'Active tab focused indicator': (c['focus'], c['canvas']), 'Active tab unfocused indicator': (c['muted'], c['canvas']),
        'Active tab text': (c['text'], c['canvas']), 'Inactive tabs': (c['placeholder'], c['chrome']),
        'URL hovered': (c['focus'], c['canvas']), 'Document map': (c['text'], c['secondary']),
        'EOL custom color': (c['placeholder'], c['canvas']), 'Non-printing characters custom color': (c['placeholder'], c['canvas']),
    }
    for style in root.find('GlobalStyles'):
        if style.get('name') in globals_:
            fg, bg = globals_[style.get('name')]
            style.set('fgColor', hexcode(fg))
            style.set('bgColor', hexcode(bg))
    ET.indent(root, space='    ')
    return '<?xml version="1.0" encoding="UTF-8" ?>\n' + ET.tostring(root, encoding='unicode') + '\n'


LAZYDOCKER = '''# T3 Chat for lazydocker, generated by scripts/t3_chat_theme.py. lazydocker only takes the
# terminal's color names, so these follow the T3 Chat terminal palette in light and dark.
gui:
  theme:
    activeBorderColor:
      - magenta
      - bold
    inactiveBorderColor:
      - default
    selectedLineBgColor:
      - reverse
    optionsTextColor:
      - magenta
'''


def outputs() -> dict:
    """Every generated file: path relative to themes/t3-chat -> contents."""
    palette = load_palette()
    license_text = (THEME / 'vscode/LICENSE.txt').read_text()
    readme = (THEME / 'vscode/README.md').read_text()
    model = (THEME / 'notepad-plus-plus/stylers.model.xml').read_text()
    out = {'vscode/package.json': json.dumps(package_json(), indent=2) + '\n'}
    plugin = {}
    for mode in MODES:
        c, ansi = palette[mode]['hex'], palette[mode]['ansi']
        pierre = json.loads((THEME / f'pierre/pierre-{mode}.json').read_text())
        syntax = syntax_colors(pierre)
        title = mode.title()
        out[f'vscode/themes/t3-chat-{mode}-color-theme.json'] = json.dumps(vscode_theme(mode, c, pierre), indent=2) + '\n'
        out[f'ghostty/T3 Chat {title}'] = ghostty_theme(c, ansi)
        out[f'xfce4-terminal/t3-chat-{mode}.theme'] = xfce_theme(mode, c, ansi)
        out[f'btop/t3-chat-{mode}.theme'] = btop_theme(c)
        out[f'jetbrains/T3 Chat {title}.icls'] = jetbrains_scheme(mode, c, syntax, ansi)
        out[f'xcode/T3 Chat {title}.xccolortheme'] = xcode_theme(c, syntax)
        out[f'notepad-plus-plus/T3 Chat {title}.xml'] = notepad_theme(c, syntax, ansi, model)
        plugin[f'themes/t3-chat-{mode}.xml'] = out[f'jetbrains/T3 Chat {title}.icls']
        plugin[f'themes/t3-chat-{mode}.theme.json'] = json.dumps(jetbrains_ui_theme(mode, c), indent=2) + '\n'
    extension = {name.removeprefix('vscode/'): data for name, data in out.items() if name.startswith('vscode/')}
    extension.update({'README.md': readme, 'LICENSE.txt': license_text})
    out[VSIX.name] = vsix(extension)
    out[JETBRAINS_PLUGIN.relative_to(THEME).as_posix()] = jetbrains_plugin(plugin)
    out['windows-terminal/t3-chat.json'] = windows_terminal(palette)
    out['lazydocker/config.yml'] = LAZYDOCKER
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
