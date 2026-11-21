"""Bounded host reads of agent-owned files, without following symlinks/FIFOs."""
import os
import stat


def read_task_file(path,limit=512*1024):
    fd=None
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size>limit:return None
        chunks=[];remaining=limit+1
        while remaining:
            chunk=os.read(fd,min(65536,remaining))
            if not chunk:break
            chunks.append(chunk);remaining-=len(chunk)
        after=os.fstat(fd);data=b''.join(chunks)
        if len(data)>limit or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):return None
        return data
    except OSError:return None
    finally:
        if fd is not None:os.close(fd)
