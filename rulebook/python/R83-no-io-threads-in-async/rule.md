---
id: R83
title: A thread for I/O in an async application is a bug, not a workaround
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs asyncio "Developing with asyncio" (concurrency and multithreading), Python docs asyncio.to_thread, Starlette docs run_in_threadpool, FastAPI docs Lifespan Events, Python docs threading (daemon threads)
---
## Rule

- In a process that already runs an event loop, I/O waits on that loop: `await` for async clients. (C1)
- A genuinely synchronous driver is called through `asyncio.to_thread` / `run_in_threadpool`. (C2)
- Spawning a `threading.Thread` to do I/O in an async application is a violation. (C3)
- Reaching a different event loop from a thread (an async client's sync bridge, or `new_event_loop` in a thread) is a violation: two loops, one pool. (C4)
- A daemon thread doing I/O is a violation: it is killed mid-write at exit and cannot be drained. (C5)
- Background work in an application with a loop is a task started by the lifespan and cancelled on shutdown. (C6)
- The stop signal is cancellation, not a polled `Event`. (C7)
- A thread is justified only when no loop exists in the process AND the work would otherwise block the caller for a user-visible time. (C8)
- A justified thread belongs to the composition root, is joined with a bounded `join(timeout)`, and is never a module-level daemon. (C9)
- Not this defect: a lock, an `Event`, a queue, or a pool of blocking database connections used from a task (synchronisation primitives). (C10)
- Not this defect: `to_thread` around one call (the documented bridge). (C11)

## Incorrect

- A service in an async app starting `threading.Thread(target=..., daemon=True)` for a polling loop.
- That thread's target opening its own `asyncio.new_event_loop()` to drive an async client.
- A `threading.Thread` subclass doing uploads in an async module.
- A module-level daemon thread started at import.
- A `threading.Timer` scheduling an upload retry in an async module.
- An `async def` calling a blocking HTTP driver directly instead of awaiting or using `to_thread` (model only).
- An async task whose stop signal is a polled `Event` (model only).

## Correct

- A poller run as `asyncio.create_task` in the lifespan and cancelled in `finally`; a blocking sensor read wrapped in `asyncio.to_thread`.
- Look-alikes: an `asyncio.Lock` and a `queue.Queue` used from tasks; `asyncio.to_thread` around one call; a CLI's
  main-thread `new_event_loop()` entry point; a test fixture creating the test's loop.

## Detection

A module "runs on a loop" when it defines an `async def` or imports `asyncio`, `anyio`, `trio`, `fastapi`,
`starlette`, `aiohttp` or `uvicorn`. In such modules `check.py` reports every `Thread(...)`/`Timer(...)` call and every
class subclassing `Thread`/`Timer` (C3; these are candidates, the model confirms they do I/O). In any module it reports
`new_event_loop()` called inside a function a thread runs — a `Thread(target=…)`/`Timer(…, f)` target or the `run`
method of a Thread subclass (C4) — and a `Thread(..., daemon=True)` created in module-level code (C9). A loop created
on the main thread, `to_thread`, locks, events and queues are never reported (C10, C11).

## LLM scan

- Confirm each detector thread hit does I/O (network, disk, database, subprocess) (C3); dismiss a thread doing only
  CPU work unless it reaches another loop (C4). A daemon thread is a C5 finding only when it does I/O; a module-level
  daemon is a C9 finding either way.
- Report blocking I/O called directly inside `async def` (a sync HTTP client, `time.sleep`, a sync DB driver, file
  I/O) without `await` on an async client (C1) or `asyncio.to_thread`/`run_in_threadpool` for a genuinely synchronous
  driver (C2).
- Report threads the detector cannot tie to a loop: a `ThreadPoolExecutor` or thread started in a sync module that an
  async application imports and calls (C3), and calls through an async client's sync bridge from such threads (C4).
- Report background loops whose stop signal is a polled `Event` or flag instead of task cancellation (C7), and
  background work not started by the lifespan or not cancelled on shutdown (C6).
- For a thread in a process with no loop, check C8 (user-visible blocking) and C9 (owned by the composition root,
  bounded `join`).
- Do not flag `asyncio.to_thread`/`run_in_threadpool` around one call, locks, events used as one-shot readiness
  signals, queues, or blocking DB pools used from tasks (C10, C11).
