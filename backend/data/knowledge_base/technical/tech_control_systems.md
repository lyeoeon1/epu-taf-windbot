# Wind Turbine Control Systems

## Overview

Modern wind turbines are highly automated machines that rely on sophisticated control systems to optimize energy capture, protect equipment from damage, ensure safe operation, and comply with grid connection requirements. The control architecture integrates multiple subsystems including supervisory control and data acquisition (SCADA), programmable logic controllers (PLC), condition monitoring systems (CMS), and power electronics. These systems work together to manage every aspect of turbine operation from blade pitch angle to grid power injection.

## SCADA (Supervisory Control and Data Acquisition)

### Purpose and Function

SCADA is the centralized system that provides operators with real-time monitoring, control, and data management capabilities for an entire wind farm. It serves as the primary human-machine interface (HMI) for wind farm operations.

### Key Functions
- **Real-time monitoring:** Display live operational data from every turbine including power output, wind speed, rotor speed, temperatures, pressures, and component status
- **Alarm management:** Collect, display, prioritize, and log alarms and warnings from all turbines. Alarms are categorized by severity (critical, major, minor, informational)
- **Remote control:** Start, stop, reset, and curtail individual turbines or groups of turbines
- **Data logging:** Record 10-minute average values, 1-second operational data, and event logs for performance analysis and reporting
- **Reporting:** Generate availability reports, production reports, power curve analysis, and regulatory compliance reports
- **Fleet management:** Compare turbine performance across the wind farm, identify underperformers, and schedule maintenance

### Architecture
- **Field level:** Sensors and actuators on each turbine communicate with the local turbine controller via industrial protocols (Modbus, Profibus, EtherCAT, CANopen)
- **Turbine level:** Each turbine controller aggregates local data and communicates with the wind farm SCADA server via Ethernet (typically fiber optic backbone)
- **Farm level:** The SCADA server collects data from all turbines, runs the farm-level controller, and provides the operator HMI
- **Remote level:** Data is transmitted to remote operations centers via secure WAN/VPN connections for centralized monitoring of multiple wind farms

### Common SCADA Platforms
- Vestas VestasOnline (proprietary)
- Siemens Gamesa Wind Farm Management System
- GE Digital Wind PowerUp
- Third-party: bazefield (DNV), Greenbyte (Engie), Windmanager

## PLC (Programmable Logic Controller)

### Purpose and Function

The PLC is the local controller installed in each turbine that executes the real-time control algorithms for turbine operation. It is the "brain" of the individual turbine, making millisecond-level decisions about pitch, yaw, power, and safety.

### Key Control Loops

**Power Control:**
- Below rated wind speed: Maximize energy capture by maintaining optimal tip speed ratio through generator torque control
- Above rated wind speed: Limit power to rated capacity through blade pitch control
- Transition zone: Smooth transition between maximum power tracking and power limiting

**Speed Control:**
- Variable-speed operation within design limits
- Overspeed protection with multiple redundant speed sensors
- Speed filtering and validation to prevent false trips

**Pitch Control:**
- Collective pitch: All three blades pitched simultaneously for power regulation
- Individual pitch control (IPC): Each blade pitched independently to reduce fatigue loads from wind shear, tower shadow, and turbulence
- Pitch rate limiting to prevent excessive structural loads
- Emergency pitch to feather on safety system activation

**Yaw Control:**
- Continuous alignment of the nacelle with the wind direction
- Yaw error measurement using wind vane(s) on the nacelle
- Dead band and time delay to prevent excessive yaw activity
- Cable twist monitoring and automatic unwinding

### Hardware
- Industrial PLC platforms: Bachmann M200/M1, Beckhoff CX series, Siemens S7, ABB AC500
- Redundant processor configurations for safety-critical functions
- Real-time operating systems with deterministic cycle times (typically 5-20 ms for main control loop)
- Safety controller (separate from main PLC) for SIL-rated safety functions per IEC 61508

## CMS (Condition Monitoring System)

### Purpose and Function

The CMS continuously monitors the health of critical mechanical and structural components to detect developing faults before they lead to catastrophic failure. CMS enables predictive maintenance, reducing unplanned downtime and preventing secondary damage.

### Monitored Components and Techniques

**Drivetrain Vibration Monitoring:**
- Accelerometers mounted on main bearing, gearbox, and generator bearings
- Measurement of vibration acceleration, velocity, and displacement
- Frequency analysis (FFT) to identify characteristic fault frequencies:
  - Bearing defect frequencies (BPFO, BPFI, BSF, FTF)
  - Gear mesh frequencies and sidebands
  - Generator electrical frequencies
- Envelope analysis for early bearing fault detection
- Trending of overall vibration levels and spectral components

**Oil Condition Monitoring:**
- Online particle counters measuring metallic debris in gearbox oil
- Oil quality sensors (moisture, temperature, dielectric constant)
- Periodic offline oil sampling for laboratory analysis (ISO 4406 cleanliness, water content, viscosity, acid number, elemental analysis)

**Structural Health Monitoring:**
- Strain gauges on blade roots for load measurement
- Tower acceleration sensors for structural mode monitoring
- Foundation tilt sensors for settlement detection
- Blade pitch bearing and yaw bearing load monitoring

**Electrical Monitoring:**
- Generator winding temperature monitoring (RTDs in stator slots)
- Partial discharge monitoring on generator windings and transformers
- Power quality monitoring (harmonics, voltage imbalance)
- Converter component temperature monitoring

### CMS Data Analysis
- Automated alarm generation based on threshold exceedances
- Trend analysis with machine learning algorithms for anomaly detection
- Remaining useful life (RUL) estimation for critical components
- Integration with CMMS (Computerized Maintenance Management System) for work order generation

## Power Electronics

### Converter Systems

The power converter is the interface between the generator and the electrical grid, controlling the flow of real and reactive power.

**Partial-Scale Converter (DFIG):**
- Rotor-side converter (RSC): Controls rotor current magnitude and frequency for speed and reactive power control
- Grid-side converter (GSC): Maintains DC link voltage and provides reactive power support
- DC link: Capacitor bank connecting RSC and GSC
- Rated at 25-30% of generator power

**Full-Scale Converter (PMSG, SCIG):**
- Generator-side converter: Rectifies variable-frequency generator output
- Grid-side converter: Inverts DC to grid-frequency AC
- DC link with capacitor bank
- Rated at 100% of generator power
- Provides full decoupling between generator and grid

### Grid Integration Requirements

Modern grid codes require wind turbines to provide:
- **Active power control:** Ramp rate limiting, frequency response, curtailment capability
- **Reactive power control:** Power factor control, voltage regulation at point of connection
- **Fault ride-through:** LVRT and HVRT capability to remain connected during grid disturbances
- **Frequency support:** Synthetic inertia and primary frequency response
- **Power quality:** Harmonic distortion limits per IEC 61000, flicker limits

## System Architecture Overview

```
[Wind Sensors] --> [Turbine PLC] --> [SCADA Server] --> [Remote Operations Center]
                       |                    |
[Pitch System] <-------+                    |
[Yaw System]  <--------+                    |
[Converter]   <--------+                    |
[Safety PLC]  <--------+                    |
                       |                    |
[CMS Sensors] --> [CMS Unit] ---------> [CMS Server] --> [Analytics Platform]
                       |
[Grid Meter]  --> [Grid Protection Relay] --> [Substation SCADA]
```

The turbine PLC communicates with all local subsystems via industrial fieldbus networks. The SCADA server aggregates data from all turbines in the wind farm. The CMS operates as a parallel system, often from a different vendor, with its own data collection and analysis infrastructure.

---

# He Thong Dieu Khien Tuabin Gio

## Tong Quan

Tuabin gio hien dai la nhung may moc tu dong hoa cao phu thuoc vao cac he thong dieu khien tinh vi de toi uu hoa thu nang luong, bao ve thiet bi khoi hu hong, dam bao van hanh an toan va tuan thu cac yeu cau ket noi luoi dien. Kien truc dieu khien tich hop nhieu he thong con bao gom SCADA, PLC, CMS va dien tu cong suat.

## SCADA (He Thong Giam Sat Dieu Khien va Thu Thap Du Lieu)

### Muc Dich va Chuc Nang

SCADA la he thong tap trung cung cap cho nguoi van hanh kha nang giam sat thoi gian thuc, dieu khien va quan ly du lieu cho toan bo trang trai gio.

### Cac Chuc Nang Chinh
- **Giam sat thoi gian thuc:** Hien thi du lieu van hanh truc tiep tu moi tuabin bao gom cong suat, toc do gio, toc do rotor, nhiet do, ap suat va trang thai thanh phan
- **Quan ly canh bao:** Thu thap, hien thi, phan loai uu tien va ghi nhat ky canh bao tu tat ca tuabin
- **Dieu khien tu xa:** Khoi dong, dung, dat lai va cat giam tung tuabin hoac nhom tuabin
- **Ghi du lieu:** Ghi lai gia tri trung binh 10 phut, du lieu van hanh 1 giay va nhat ky su kien
- **Bao cao:** Tao bao cao kha dung, bao cao san luong, phan tich duong cong cong suat

### Kien Truc
- **Cap truong:** Cam bien va co cau chap hanh tren moi tuabin giao tiep voi bo dieu khien cuc bo qua giao thuc cong nghiep (Modbus, Profibus, EtherCAT)
- **Cap tuabin:** Moi bo dieu khien tuabin tong hop du lieu cuc bo va giao tiep voi may chu SCADA qua Ethernet
- **Cap trang trai:** May chu SCADA thu thap du lieu tu tat ca tuabin va cung cap giao dien nguoi-may
- **Cap tu xa:** Du lieu duoc truyen den trung tam van hanh tu xa qua ket noi WAN/VPN bao mat

## PLC (Bo Dieu Khien Logic Lap Trinh)

### Muc Dich va Chuc Nang

PLC la bo dieu khien cuc bo duoc cai dat trong moi tuabin thuc hien cac thuat toan dieu khien thoi gian thuc. No la "bo nao" cua tung tuabin, dua ra cac quyet dinh cap mili-giay ve goc canh, quay huong, cong suat va an toan.

### Cac Vong Dieu Khien Chinh

**Dieu Khien Cong Suat:**
- Duoi toc do gio dinh muc: Toi da hoa thu nang luong bang cach duy tri ty so toc do dau canh toi uu
- Tren toc do gio dinh muc: Gioi han cong suat o cong suat dinh muc thong qua dieu khien goc canh

**Dieu Khien Goc Canh:**
- Goc canh tap the: Ca ba canh quay dong thoi de dieu tiet cong suat
- Dieu khien goc canh rieng le (IPC): Moi canh quay doc lap de giam tai trong moi
- Goc canh khan cap ve vi tri la khi he thong an toan kich hoat

**Dieu Khien Quay Huong:**
- Can chinh lien tuc vo tuabin voi huong gio
- Do sai so quay huong su dung chong gio tren vo tuabin
- Giam sat xoan cap va tu dong thao xoan

## CMS (He Thong Giam Sat Tinh Trang)

### Muc Dich va Chuc Nang

CMS giam sat lien tuc suc khoe cua cac thanh phan co khi va ket cau quan trong de phat hien cac loi dang phat trien truoc khi chung dan den hu hong nghiem trong. CMS cho phep bao tri du doan, giam thoi gian ngung ngoai ke hoach.

### Cac Thanh Phan va Ky Thuat Giam Sat

**Giam Sat Rung Dong He Truyen Dong:**
- Cam bien gia toc gan tren vong bi chinh, hop so va vong bi may phat
- Do gia toc, van toc va do dich chuyen rung dong
- Phan tich tan so (FFT) de xac dinh tan so loi dac trung

**Giam Sat Tinh Trang Dau:**
- Bo dem hat truc tuyen do manh vu kim loai trong dau hop so
- Cam bien chat luong dau (do am, nhiet do, hang so dien moi)
- Lay mau dau dinh ky de phan tich phong thi nghiem

**Giam Sat Suc Khoe Ket Cau:**
- Cam bien bien dang tai goc canh de do tai trong
- Cam bien gia toc thap de giam sat che do ket cau
- Cam bien nghieng mong de phat hien lun

## Dien Tu Cong Suat

### He Thong Bien Doi

Bo bien doi cong suat la giao dien giua may phat va luoi dien, dieu khien dong cong suat thuc va phan khang.

**Bo Bien Doi Mot Phan (DFIG):**
- Bo bien doi phia rotor (RSC): Dieu khien dong dien rotor de dieu khien toc do va cong suat phan khang
- Bo bien doi phia luoi (GSC): Duy tri dien ap DC link va ho tro cong suat phan khang
- Dinh muc 25-30% cong suat may phat

**Bo Bien Doi Toan Phan (PMSG, SCIG):**
- Bo bien doi phia may phat: Chinh luu dau ra tan so thay doi
- Bo bien doi phia luoi: Nghich luu DC thanh AC tan so luoi
- Dinh muc 100% cong suat may phat
- Cung cap tach roi hoan toan giua may phat va luoi

### Yeu Cau Tich Hop Luoi

Cac quy tac luoi dien hien dai yeu cau tuabin gio cung cap:
- **Dieu khien cong suat tac dung:** Gioi han toc do tang, dap ung tan so, kha nang cat giam
- **Dieu khien cong suat phan khang:** Dieu khien he so cong suat, dieu chinh dien ap tai diem ket noi
- **Vuot qua su co:** Kha nang LVRT va HVRT de duy tri ket noi trong cac nhieu loan luoi
- **Ho tro tan so:** Quan tinh tong hop va dap ung tan so so cap
- **Chat luong dien nang:** Gioi han meo hai hoa theo IEC 61000
