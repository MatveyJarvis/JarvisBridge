
# TODO: Коннектор к 1С (файловый/COM/HTTP). Оставлен плейсхолдер до Этапа 2+.
class OneCConnector:
    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string

    def export_to_csv(self, query: str, out_path: str):
        raise NotImplementedError("Реализация будет добавлена на следующем этапе.")
