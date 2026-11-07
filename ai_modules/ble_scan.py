import asyncio
import sys

HR_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
HR_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"


async def scan():
    from bleak import BleakScanner
    print("Scanning for 10 seconds...\n")
    found = await BleakScanner.discover(timeout=10.0, return_adv=True)
    rows = []
    for addr, (dev, adv) in found.items():
        rows.append((adv.rssi if adv.rssi is not None else -999,
                     dev.name or adv.local_name or "(no name)", addr,
                     [u.lower() for u in (adv.service_uuids or [])]))
    rows.sort(reverse=True)
    for rssi, name, addr, uuids in rows:
        flag = "   <-- advertises HEART RATE" if HR_SERVICE in uuids else ""
        print(f"{rssi:>5} dBm  {name:<30} {addr}{flag}")
    print(f"\n{len(rows)} devices found.")


async def inspect(name_part):
    from bleak import BleakScanner, BleakClient
    for attempt in range(1, 4):
        print(f"\nAttempt {attempt}/3: looking for '{name_part}'...")
        dev = await BleakScanner.find_device_by_filter(
            lambda d, ad: name_part.lower() in ((d.name or ad.local_name or "").lower()),
            timeout=15.0)
        if dev is None:
            print("Not found. Wake the watch screen and try again.")
            continue
        print(f"Found: {dev.name}  {dev.address}  - connecting (up to 40 s)...")
        try:
            async with BleakClient(dev, timeout=40.0) as client:
                print("Connected. Services:\n")
                has_hr = False
                for s in client.services:
                    tag = "   <-- HEART RATE SERVICE" if s.uuid.lower() == HR_SERVICE else ""
                    has_hr = has_hr or bool(tag)
                    print(f"Service {s.uuid}{tag}")
                    for c in s.characteristics:
                        mark = "  <-- heart rate measurement" if c.uuid.lower() == HR_CHAR else ""
                        print(f"    {c.uuid}  {','.join(c.properties)}{mark}")
                print()
                if has_hr:
                    print("RESULT: standard Heart Rate service FOUND.")
                    print(f'Run: python ai_modules/heart_monitor.py --source ble --ble-name "{name_part}" --age 20')
                else:
                    print("RESULT: connected, but NO standard Heart Rate service on this watch.")
                return
        except Exception as exc:
            print(f"Could not connect: {type(exc).__name__}: {exc!r}")
            await asyncio.sleep(3)
    print("\nRESULT: could not connect after 3 attempts.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(inspect(sys.argv[1]))
    else:
        asyncio.run(scan())