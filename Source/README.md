# IoT Telemetry Pipeline — Source

A prototype IoT telemetry system built with Python AsyncIO for the NET322 Network Programming & Applications Development assignment.

The system simulates greenhouse sensors that continuously send telemetry readings to a central server using Protobuf over TCP, while providing a REST API and WebSocket live feed for monitoring and historical data access.

---

# Project Structure

```text
Source/
├── client/                 Sensor simulator
├── config/                 YAML configuration files
├── frontend/               Dashboard UI
├── proto/                  Protobuf schema
├── server/                 TCP ingest + REST API
├── wss/                    WebSocket server
├── telemetry.db            SQLite database
├── requirements.txt
└── README.md
```

---

# Technologies Used

* Python AsyncIO
* TCP Sockets
* REST API
* WebSocket
* SQLite
* YAML
* JSON
* XML
* aiohttp

---

# Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Compile protobuf schema:

```bash
protoc --python_out=. proto/telemetry.proto
```

---

# Running the System

Open multiple terminals inside the `Source/` directory.

---

## 1. Start the Telemetry Server

```bash
python -m server
```

Expected output:

```text
=== IoT Telemetry System Started ===
REST API : http://127.0.0.1:8080
TCP Port : 9000
Waiting for sensor connections..........!
```

The server:

* accepts TCP sensor connections
* decodes Protobuf messages
* stores readings in SQLite

---

## 2. Start the WebSocket Server

```bash
python -m wss
```

Expected output:

```text
=== WebSocket Live Feed Started ===
1.WebSocket URL : ws://0.0.0.0:8765/live
2.Waiting for dashboard clients............!
```



---

## 3. Start the Sensor Simulator

```bash
python -m client --config config/sensors.yaml
```

Example output:

```text
[temp-1  ] temperature  = 29.44 C
[humid-1 ] humidity     = 72.81 %
[soil-1  ] moisture     = 61.22 %

----------------------------------------
```

The simulator:

* loads sensor settings from YAML
* generates realistic readings
* serializes readings using Protobuf
* sends telemetry over TCP asynchronously

---

# REST API

Supported formats:

* JSON
* XML
* YAML

The API performs content negotiation using the `Accept` header.

---

# REST Endpoints

| Method | Endpoint                 | Description                 |
| ------ | ------------------------ | --------------------------- |
| GET    | `/sensors`               | List all registered sensors |
| GET    | `/sensors/{id}/readings` | Get historical readings     |
| POST   | `/sensors`               | Register a new sensor       |
| DELETE | `/sensors/{id}`          | Remove a sensor             |

---

#  VERIFY REST API 

---

## JSON Request

```powershell
iwr http://localhost:8080/sensors `
-Headers @{Accept="application/json"} `
-UseBasicParsing
```

---

## XML Request

```powershell
iwr http://localhost:8080/sensors `
-Headers @{Accept="application/xml"} `
-UseBasicParsing
```

---

## YAML Request

```powershell
iwr http://localhost:8080/sensors `
-Headers @{Accept="application/yaml"} `
-UseBasicParsing
```

---

## Register a Sensor

```powershell
$body = '{"id":"test-1","type":"temperature"}'

iwr `
-Uri http://localhost:8080/sensors `
-Method POST `
-Body $body `
-ContentType "application/json" `
-UseBasicParsing
```

## Get All Sensors

```powershell
iwr http://localhost:8080/sensors `
-UseBasicParsing
```

---

## Get Historical Readings

```powershell
iwr http://localhost:8080/sensors/temp-1/readings `
-UseBasicParsing
```
---

## Delete a Sensor

```powershell
iwr `
-Uri http://localhost:8080/sensors/test-1 `
-Method DELETE `
-UseBasicParsing
```

---

# Cookies

The REST API uses cookies to identify client sessions.

Example response header:

```text
Set-Cookie: session_id=xxxxx; HttpOnly; Path=/
```

---

# Database

The system uses SQLite (`GreenHouse.db`) for persistent storage.

Stored data includes:
* registered sensors
* historical telemetry readings

---


---

# Authors

* Alex Elijah — BSC-COM-NE-19-23
* Robert Lupiya — BSC-COM-NE-13-23
