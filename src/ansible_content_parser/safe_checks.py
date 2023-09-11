"""Check if a given archive (zip/tar) file is safe."""

# Ref: https://sonarcloud.io/organizations/ansible/rules?open=python%3AS5042&rule_key=python%3AS5042&tab=how_to_fix
import zipfile


threshold_entries = 10000
threshold_size = 1000000000
threshold_ratio = 100


def check_zip_file_is_safe(source: str) -> None:
    """Make sure that expanding the zip file is safe."""
    if not zipfile.is_zipfile(source):
        msg = f"{source} is not a valid zip file."
        raise RuntimeError(
            msg,
        )

    total_size_archive = 0
    total_entry_archive = 0

    with zipfile.ZipFile(source, "r") as f:
        for info in f.infolist():
            data = f.read(info)
            total_entry_archive += 1

            total_size_archive = total_size_archive + len(data)
            ratio = len(data) / info.compress_size
            if ratio > threshold_ratio:
                msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                raise RuntimeError(
                    msg,
                )

            if total_entry_archive > threshold_entries:
                msg = "too much entries in this archive, can lead to inodes exhaustion of the system"
                raise RuntimeError(
                    msg,
                )

            if total_size_archive > threshold_size:
                msg = "the uncompressed data size is too much for the application resource capacity"
                raise RuntimeError(
                    msg,
                )
