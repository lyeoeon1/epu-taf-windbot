# Wind Turbine Emergency Shutdown Procedures

## Overview

Wind turbines are equipped with multiple shutdown mechanisms to protect equipment, personnel, and the electrical grid. Understanding the different types of shutdowns, their triggers, and the correct procedures for post-shutdown assessment and restart is essential for all wind farm operations personnel. Improper shutdown handling can lead to component damage, extended downtime, or safety hazards.

## Types of Shutdowns

### Normal Shutdown

A normal shutdown is a controlled, planned stop of the turbine. The control system reduces power output gradually, pitches the blades to feather position (approximately 90 degrees), and applies the mechanical brake once the rotor has reached a low speed.

**Common triggers:**
- Scheduled maintenance requiring turbine lockout
- Wind speed below cut-in threshold (typically 3-4 m/s) for extended period
- Wind speed above cut-out threshold (typically 25 m/s) sustained for the defined duration
- Operator-initiated stop via SCADA for non-emergency reasons
- Grid operator curtailment request

**Sequence:**
1. Control system receives stop command
2. Generator torque is reduced gradually over 30-60 seconds
3. Blade pitch is adjusted toward feather position (90 degrees)
4. Rotor speed decreases as aerodynamic torque is removed
5. Generator is disconnected from the grid at low rotor speed
6. Mechanical brake is applied once rotor speed is below threshold (typically below 2 RPM)
7. Yaw system is locked
8. Turbine status is set to "Stopped - Normal" in SCADA

### Emergency Shutdown (E-Stop)

An emergency shutdown is an immediate, rapid stop of the turbine triggered by safety-critical conditions. The blades are pitched to feather as fast as the pitch system allows, and the mechanical brake is applied simultaneously or shortly after.

**Common triggers:**
- Manual E-stop button pressed (tower base, nacelle, or hub)
- Overspeed detection (rotor speed exceeds rated speed by a defined margin, typically 110-120%)
- Excessive vibration detected by accelerometers
- Fire or smoke detection in nacelle, hub, or tower
- Pitch system malfunction (one or more blades unable to pitch)
- Yaw system runaway
- Generator or converter overtemperature
- Loss of communication between controller and safety system
- Structural integrity alarm (tower acceleration, blade integrity)

**Sequence:**
1. Safety controller activates emergency stop relay
2. All three blades receive simultaneous pitch-to-feather command at maximum pitch rate
3. Pitch system backup (battery or accumulator) activates if main hydraulic/electric power is lost
4. Mechanical brake is applied immediately or when rotor speed drops below a defined threshold
5. Generator is disconnected from the grid immediately
6. Yaw brake is engaged
7. All auxiliary systems remain powered for monitoring
8. Alarm is transmitted to SCADA and operations center
9. Turbine status is set to "Stopped - Emergency" in SCADA
10. Turbine is locked out and cannot be restarted remotely without investigation

### Grid Fault Shutdown

A grid fault shutdown occurs when the electrical grid experiences a disturbance that requires the turbine to disconnect. Modern turbines are equipped with Low Voltage Ride-Through (LVRT) and High Voltage Ride-Through (HVRT) capabilities, but shutdowns occur when faults exceed these thresholds.

**Common triggers:**
- Grid voltage drops below LVRT threshold for longer than the defined ride-through period
- Grid voltage exceeds HVRT threshold
- Grid frequency deviation beyond acceptable range (typically outside 47.5-51.5 Hz for 50 Hz grids)
- Loss of grid connection (islanding detection)
- Phase imbalance exceeding defined limits

**Sequence:**
1. Grid monitoring system detects fault condition
2. Turbine attempts LVRT/HVRT if within capability
3. If fault persists beyond ride-through capability, turbine initiates controlled shutdown
4. Reactive power support is provided during ride-through period per grid code
5. Generator is disconnected from the grid
6. Blades are pitched to reduce rotor speed
7. Turbine enters standby mode, monitoring grid conditions
8. Automatic restart is initiated when grid parameters return to normal range

## Post-Shutdown Checks

After any shutdown, specific checks must be performed before the turbine can be returned to service.

### After Normal Shutdown
- Verify turbine is in safe, locked-out condition if maintenance is to be performed
- Confirm blade pitch angles are at feather position
- Verify mechanical brake is engaged
- Check SCADA for any alarms that may have triggered during shutdown sequence

### After Emergency Shutdown
- **Do not attempt remote restart.** An on-site investigation is mandatory.
- Review the SCADA event log and safety system log to identify the root cause
- Perform a physical inspection of the turbine:
  - Check for signs of fire, smoke, or burning smell
  - Inspect visible components for damage (blades, tower, nacelle exterior)
  - Check brake disc temperature (may be elevated after emergency braking)
  - Inspect pitch system: verify all three blades reached feather position
  - Check for oil leaks in hydraulic systems
  - Inspect electrical connections for signs of arcing or overheating
- Document all findings with photographs
- Correct the root cause before attempting restart
- Test all safety systems before returning to service

### After Grid Fault Shutdown
- Verify grid voltage and frequency have returned to normal operating range
- Check converter and transformer for any fault codes
- Review event log for the sequence of events during the grid fault
- Verify that the turbine control system has returned to ready-to-start status
- If automatic restart is enabled and grid conditions are normal, the turbine may restart automatically after a configurable delay (typically 1-10 minutes)

## Restart Procedures

### Standard Restart After Normal Shutdown
1. Verify all maintenance activities are complete and signed off
2. Remove all lockout/tagout devices
3. Close all access doors and hatches
4. Verify no personnel are inside the turbine
5. Release mechanical brake
6. Release yaw brake
7. Enable pitch control system
8. Set turbine to "Remote" or "Auto" mode via SCADA
9. Turbine will start automatically when wind conditions are within operating range

### Restart After Emergency Shutdown
1. Complete all post-shutdown investigation and corrective actions
2. Document the root cause and corrective action in the maintenance log
3. Obtain authorization from the site manager or operations lead
4. Perform pre-start safety checks:
   - Test all E-stop buttons and verify they activate the safety relay
   - Verify pitch system operates correctly in both directions
   - Check brake system function
   - Verify all sensor readings are within normal range
5. Reset the safety system
6. Perform a controlled start with on-site personnel monitoring
7. Monitor the first hour of operation closely for any recurrence

---

# Quy Trinh Dung Khan Cap Tuabin Gio

## Tong Quan

Tuabin gio duoc trang bi nhieu co che dung may de bao ve thiet bi, nhan su va luoi dien. Viec hieu cac loai dung may khac nhau, cac yeu to kich hoat va quy trinh dung de danh gia sau khi dung may va khoi dong lai la dieu can thiet cho tat ca nhan vien van hanh trang trai gio.

## Cac Loai Dung May

### Dung May Binh Thuong

Dung may binh thuong la viec dung tuabin co kiem soat va theo ke hoach. He thong dieu khien giam dan cong suat, quay canh ve vi tri la (khoang 90 do) va ap dung phanh co khi khi rotor dat toc do thap.

**Cac yeu to kich hoat pho bien:**
- Bao tri theo lich yeu cau khoa tuabin
- Toc do gio duoi nguong cat vao (thuong 3-4 m/s) trong thoi gian keo dai
- Toc do gio tren nguong cat ra (thuong 25 m/s) duy tri trong thoi gian xac dinh
- Nguoi van hanh chu dong dung qua SCADA
- Yeu cau cat giam tu nguoi van hanh luoi dien

**Trinh tu:**
1. He thong dieu khien nhan lenh dung
2. Mo-men may phat duoc giam dan trong 30-60 giay
3. Goc canh duoc dieu chinh ve vi tri la (90 do)
4. Toc do rotor giam khi mo-men khi dong hoc bi loai bo
5. May phat duoc ngat khoi luoi dien o toc do rotor thap
6. Phanh co khi duoc ap dung khi toc do rotor duoi nguong (thuong duoi 2 RPM)
7. He thong quay huong duoc khoa
8. Trang thai tuabin duoc dat la "Dung - Binh Thuong" trong SCADA

### Dung Khan Cap (E-Stop)

Dung khan cap la viec dung tuabin ngay lap tuc, nhanh chong do cac dieu kien quan trong ve an toan kich hoat.

**Cac yeu to kich hoat pho bien:**
- Nut E-stop duoc nhan (chan thap, vo tuabin hoac hub)
- Phat hien qua toc do (toc do rotor vuot qua toc do dinh muc, thuong 110-120%)
- Rung dong qua muc duoc phat hien boi cam bien gia toc
- Phat hien chay hoac khoi trong vo tuabin, hub hoac thap
- Truc trac he thong goc canh
- He thong quay huong mat kiem soat
- Qua nhiet may phat hoac bo bien doi

**Trinh tu:**
1. Bo dieu khien an toan kich hoat relay dung khan cap
2. Ca ba canh nhan lenh quay ve vi tri la dong thoi o toc do goc toi da
3. Nguon du phong he thong goc canh (pin hoac binh tich) kich hoat neu mat nguon chinh
4. Phanh co khi duoc ap dung ngay lap tuc hoac khi toc do rotor giam
5. May phat duoc ngat khoi luoi dien ngay lap tuc
6. Phanh quay huong duoc kich hoat
7. Canh bao duoc truyen den SCADA va trung tam van hanh
8. Tuabin khong the khoi dong lai tu xa ma khong co dieu tra

### Dung May Do Loi Luoi Dien

Dung may do loi luoi dien xay ra khi luoi dien gap nhieu loan yeu cau tuabin ngat ket noi. Tuabin hien dai co kha nang Vuot Qua Dien Ap Thap (LVRT) va Vuot Qua Dien Ap Cao (HVRT), nhung dung may xay ra khi loi vuot qua cac nguong nay.

**Cac yeu to kich hoat pho bien:**
- Dien ap luoi giam duoi nguong LVRT lau hon thoi gian vuot qua xac dinh
- Dien ap luoi vuot qua nguong HVRT
- Sai lech tan so luoi ngoai pham vi chap nhan (thuong ngoai 47.5-51.5 Hz cho luoi 50 Hz)
- Mat ket noi luoi (phat hien dao)

## Kiem Tra Sau Khi Dung May

### Sau Khi Dung Khan Cap
- **Khong thu khoi dong lai tu xa.** Dieu tra tai cho la bat buoc.
- Xem xet nhat ky su kien SCADA va nhat ky he thong an toan de xac dinh nguyen nhan goc
- Thuc hien kiem tra vat ly tuabin:
  - Kiem tra dau hieu chay, khoi hoac mui chay
  - Kiem tra cac thanh phan nhin thay co hu hong khong
  - Kiem tra nhiet do dia phanh
  - Kiem tra he thong goc canh
  - Kiem tra ro ri dau trong he thong thuy luc
  - Kiem tra cac ket noi dien xem co dau hieu ho quang hoac qua nhiet
- Ghi lai tat ca phat hien bang hinh anh
- Khac phuc nguyen nhan goc truoc khi khoi dong lai

## Quy Trinh Khoi Dong Lai

### Khoi Dong Lai Sau Dung Khan Cap
1. Hoan thanh tat ca dieu tra va hanh dong khac phuc
2. Ghi lai nguyen nhan goc va hanh dong khac phuc trong nhat ky bao tri
3. Lay uy quyen tu quan ly cong truong hoac truong van hanh
4. Thuc hien kiem tra an toan truoc khi khoi dong:
   - Thu tat ca nut E-stop
   - Xac nhan he thong goc canh hoat dong chinh xac
   - Kiem tra chuc nang he thong phanh
   - Xac nhan tat ca so lieu cam bien trong pham vi binh thuong
5. Dat lai he thong an toan
6. Thuc hien khoi dong co kiem soat voi nhan vien giam sat tai cho
7. Giam sat chat che gio dau tien van hanh
