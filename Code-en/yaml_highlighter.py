# yaml_highlighter.py
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

class YamlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((QRegularExpression(r"\b[0-9]+\b"), number_format))
        # 字符串格式 (带引号)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["id", "info", "name", "author", "severity", "description", "reference",
                    "classification", "metadata", "tags", "requests", "http", "dns", "file",
                    "network", "headless", "websocket", "matchers", "extractors", "-", "type", "part",
                    "words", "status", "body", "header", "method", "path", "raw"]
        for word in keywords:
            self.highlighting_rules.append((QRegularExpression(rf"\b{word}:"), keyword_format))
        self.highlighting_rules.append((QRegularExpression(r"^\s*-\s"), keyword_format))
        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)