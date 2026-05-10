import win32clipboard


def copy_html_to_clipboard(html: str) -> None:
    CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

    html_body = f"<html><body>{html}</body></html>"
    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:08d}\r\n"
        "EndHTML:{end_html:08d}\r\n"
        "StartFragment:{start_frag:08d}\r\n"
        "EndFragment:{end_frag:08d}\r\n"
    )

    dummy_header = header_template.format(
        start_html=0, end_html=0, start_frag=0, end_frag=0
    )
    start_html = len(dummy_header)
    start_frag = start_html + html_body.index("<html>")
    end_frag = start_html + html_body.index("</body>") + len("</body>")
    end_html = start_html + len(html_body)

    header = header_template.format(
        start_html=start_html,
        end_html=end_html,
        start_frag=start_frag,
        end_frag=end_frag,
    )
    data = (header + html_body).encode("utf-8")

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(CF_HTML, data)
    win32clipboard.CloseClipboard()
