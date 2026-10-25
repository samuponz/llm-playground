# Linux processes cheatsheet

Commands for the host (your laptop). Most also work inside containers that include them.

## `ps`: a snapshot of running programs

| Command | What it shows |
|---|---|
| `ps` | only the processes of **this terminal** (your shell and `ps` itself) |
| `ps -e` | every process on the machine |
| `ps aux` | every process, with user, CPU, memory (RSS) and full command |
| `ps aux \| grep ollama` | find one program |
| `ps -o pid,user,rss,cmd -p <pid>` | details for one process ID |

## `top`: live view

```
top - 19:57:51 up 1 day,  1 user,  load average: 2,48, 2,17, 1,62
Tasks: 362 total,   1 running, 361 sleeping
%Cpu(s):  3,0 us,  1,5 sy, 94,7 id,  0,8 wa
MiB Mem :  15877 total,  480 free,  7354 used,  8041 buff/cache   8159 avail Mem
MiB Swap:   1937 total, 1511 free,   425 used
```

| Line | Meaning |
|---|---|
| up | time since boot |
| load average | processes wanting the CPU, averaged over 1 / 5 / 15 minutes (4 cores: 4.0 = fully busy) |
| Tasks | most processes are **sleeping** = waiting for input, network, a timer |
| %Cpu | `us` your programs, `sy` the kernel working for them, `id` idle, `wa` waiting for the disk |
| Mem | "free" is low on purpose: Linux uses spare RAM as **cache** and gives it back on demand. Look at **avail Mem** |
| Swap | disk used as overflow memory: a little is normal, a lot makes everything slow |

| Column | Meaning |
|---|---|
| **RES** | real memory used: the one to watch |
| VIRT | memory reserved, not used (VS Code shows ~1.4 TB: ignore it) |
| S | `R` running, `S` sleeping, `I` idle kernel thread, `Z` zombie |
| COMMAND | `systemd` is PID 1 (first process at boot); `kworker`, `kthreadd` are the kernel's own workers |

Keys inside `top`: `M` sort by memory · `P` sort by CPU · `1` per-core CPU · `q` quit.

## `/proc`: where these tools get their numbers

`/proc` is not on disk: the kernel generates each file when you read it. `ps` and `top`
just read and format it.

```bash
ls /proc                      # one folder per process ID
cat /proc/<pid>/cmdline; echo # the command a process was started with
cat /proc/<pid>/cgroup        # its cgroup (docker-....scope for container processes)
cat /proc/loadavg             # the load average
grep MemAvailable /proc/meminfo
```

## Try this

Run `top`, press `M`, then ask the chat a question in another terminal: `ollama` jumps to
the top as the model loads (1–3 GB of RES). `docker stats` and `ollama ps` show the same
moment from their own point of view.
