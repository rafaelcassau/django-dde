import csv
import tempfile
import codecs

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _
from model_utils.choices import Choices

from .utils import ExporterHelper


class FileHandler:
    VALID_HANDLERS = Choices(
        ("default_storage", _("default_storage"))
    )

    def __init__(self, exporter, path_name, target_storage='default_storage'):
        self.path_name = path_name
        self.exporter = exporter
        self.target = self._get_file_storage(target_storage)

    def proccess(self):
        if self.target == self.VALID_HANDLERS.default_storage:
            self._proccess_default_storage()

    def _get_file_storage(self, storage):
        if storage not in self.VALID_HANDLERS:
            raise KeyError(_("Invalid or unsupported storage"))

        return storage

    def _proccess_default_storage(self):
        """ Join the file_list (chunked files) into one then saves and return the saved path """
        header = ExporterHelper.get_header(self.exporter.attrs)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=True, encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=str(';'), quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            f.flush()

            for chunk in self.exporter.chunks.all():
                with default_storage.open(chunk.file.name) as temp_file:
                    reader = csv.reader(codecs.iterdecode(temp_file, 'utf-8'))
                    for row in reader:
                        writer.writerow(row[0].split(';'))
                        f.flush()

            # TODO search for better solution
            # need to be a binary file, but csv.writerow can't write binary, try user DictWriter subclass
            readble_file = open(f.name, 'rb').read()

            self.exporter.file.save(self.path_name, ContentFile(readble_file))

        return self.exporter
