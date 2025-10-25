import csv, os
from datetime import datetime

class DailyCSV:
    def __init__(self, outdir="./logs", header=None, prefix="log"):
        self.outdir = outdir; self.header = header; self.prefix = prefix
        os.makedirs(outdir, exist_ok=True)
        self.fp = None; self.writer = None; self.current = None

    def _path(self):
        d = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.outdir, f"{self.prefix}_{d}.csv")

    def _rotate(self):
        path = self._path()
        if path != self.current:
            if self.fp: self.fp.close()
            new = not os.path.exists(path)
            self.fp = open(path, "a", newline="")
            self.writer = csv.writer(self.fp)
            if new and self.header: self.writer.writerow(self.header)
            self.current = path
            print("Logging to", path)

    def write(self, row):
        self._rotate()
        self.writer.writerow(row); self.fp.flush()

    def close(self):
        if self.fp: self.fp.close()
