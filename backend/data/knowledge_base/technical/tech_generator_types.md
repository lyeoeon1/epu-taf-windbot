# Wind Turbine Generator Types

## Overview

The generator is the component that converts the mechanical rotational energy of the wind turbine rotor into electrical energy. The choice of generator type fundamentally affects the entire drivetrain design, power electronics requirements, grid connection strategy, and overall turbine performance. Three main generator types dominate the wind energy industry: the Doubly-Fed Induction Generator (DFIG), the Permanent Magnet Synchronous Generator (PMSG), and the Squirrel Cage Induction Generator (SCIG).

## Doubly-Fed Induction Generator (DFIG)

### Operating Principle

The DFIG is a wound-rotor induction generator where both the stator and rotor windings are electrically active. The stator is connected directly to the grid, while the rotor is connected to the grid through a partial-scale power converter (typically rated at 25-30% of the generator's rated power). By controlling the frequency and magnitude of the rotor currents, the DFIG can operate at variable speeds while maintaining grid-frequency output on the stator.

### Key Characteristics
- **Speed range:** Typically +/- 30% around synchronous speed
- **Converter rating:** 25-30% of rated power (partial-scale converter)
- **Gearbox:** Required (three-stage gearbox is standard, converting ~15 RPM rotor speed to ~1500/1800 RPM generator speed)
- **Slip rings and brushes:** Required for rotor electrical connection (maintenance item)
- **Reactive power control:** Capable of providing reactive power to the grid through rotor-side converter

### Advantages
- Lower power converter cost due to partial-scale rating
- Proven technology with decades of operational history
- Good reactive power control capability
- Lower converter losses compared to full-scale converter systems
- Well-established supply chain and service infrastructure

### Disadvantages
- Requires a multi-stage gearbox (a major maintenance and failure component)
- Slip rings and brushes require periodic replacement (every 6-12 months in some designs)
- Limited fault ride-through capability without additional protection (crowbar circuit)
- Narrower speed range compared to full-converter systems
- Gearbox noise and vibration

### Applications
- Widely used in 1.5-3 MW class turbines
- Dominant technology from 2000-2015
- Still used in cost-sensitive markets and onshore applications
- Examples: Vestas V90, GE 1.5sle, Siemens Gamesa G114

## Permanent Magnet Synchronous Generator (PMSG)

### Operating Principle

The PMSG uses permanent magnets (typically neodymium-iron-boron, NdFeB) mounted on the rotor to create the magnetic field, eliminating the need for rotor electrical excitation. The stator windings produce AC power at a frequency proportional to rotor speed. A full-scale power converter between the generator and grid converts this variable-frequency output to grid frequency.

### Key Characteristics
- **Speed range:** Full variable speed (0 to rated speed and above)
- **Converter rating:** 100% of rated power (full-scale converter)
- **Gearbox:** Can be direct-drive (no gearbox) or use a single-stage or two-stage gearbox (medium-speed PMSG)
- **Slip rings:** Not required (no electrical rotor connection)
- **Excitation:** Permanent magnets, no external excitation power needed

### Configurations

**Direct-Drive PMSG:**
- Generator operates at rotor speed (8-20 RPM for utility-scale turbines)
- Very large diameter generator (4-8 meters) with high pole count
- No gearbox, eliminating a major failure mode
- Higher generator cost but lower drivetrain maintenance
- Examples: Siemens Gamesa SG 8.0-167 DD, Enercon E-126, GE Haliade-X

**Medium-Speed PMSG:**
- Single-stage or two-stage gearbox (gear ratio 1:10 to 1:40)
- Generator operates at 100-400 RPM
- Smaller generator than direct-drive, lighter nacelle
- Simplified gearbox with fewer stages and higher reliability than three-stage
- Examples: Vestas V236-15.0, some Mingyang designs

### Advantages
- Higher efficiency across the operating range (no rotor copper losses)
- No slip rings or brushes (reduced maintenance)
- Full speed range via full-scale converter
- Superior grid fault ride-through capability
- Direct-drive configuration eliminates gearbox failures
- Better partial-load efficiency
- Lower noise (especially direct-drive)

### Disadvantages
- Full-scale converter is more expensive than partial-scale
- Permanent magnets use rare-earth materials (neodymium, dysprosium) with supply chain and price volatility concerns
- Direct-drive generators are very large and heavy (nacelle weight can be 400+ tonnes)
- Risk of permanent magnet demagnetization at high temperatures
- Difficult to demagnetize for maintenance (always-on magnetic field)
- Higher converter losses at full load compared to DFIG

### Applications
- Dominant technology for offshore wind turbines (5-15+ MW class)
- Increasingly used in large onshore turbines
- Preferred for harsh environments where gearbox maintenance is difficult
- Current industry trend toward medium-speed PMSG as a balance of benefits

## Squirrel Cage Induction Generator (SCIG)

### Operating Principle

The SCIG is the simplest generator type. It has a stator with grid-connected windings and a rotor consisting of aluminum or copper bars short-circuited by end rings (resembling a squirrel cage). The rotor has no electrical connection. The SCIG operates at nearly constant speed (slip of 1-2% above synchronous speed) in fixed-speed applications, or at variable speed when paired with a full-scale converter.

### Key Characteristics
- **Speed range:** Fixed speed (1-2% slip) or full variable speed with full-scale converter
- **Converter rating:** 0% (fixed speed, direct grid connection) or 100% (variable speed with full converter)
- **Gearbox:** Required (three-stage for fixed speed, can vary for variable speed)
- **Slip rings:** Not required
- **Construction:** Extremely robust and simple

### Advantages
- Lowest generator cost and simplest construction
- Extremely robust with minimal maintenance requirements
- No slip rings, no brushes, no permanent magnets
- No rare-earth material supply chain risk
- Well-proven technology in industrial applications
- Easy to manufacture and repair

### Disadvantages
- Fixed-speed operation limits energy capture (without full converter)
- Requires full-scale converter for variable-speed operation (negating cost advantage)
- Lower efficiency than PMSG due to rotor losses
- Requires reactive power compensation (capacitor banks or converter)
- Larger and heavier than equivalent PMSG for same power rating
- Cannot provide reactive power without external compensation

### Applications
- Used in older fixed-speed turbines (Vestas V47, V52; Bonus/Siemens early models)
- Some modern variable-speed designs with full converter (Siemens Gamesa SWT series)
- Preferred where supply chain independence from rare-earth materials is important

## Comparison Summary

| Feature | DFIG | PMSG (Direct-Drive) | PMSG (Medium-Speed) | SCIG |
|---|---|---|---|---|
| Converter size | Partial (30%) | Full (100%) | Full (100%) | None or Full |
| Gearbox | 3-stage | None | 1-2 stage | 3-stage |
| Speed range | +/- 30% | Full | Full | Fixed or Full |
| Maintenance | Moderate | Low (no gearbox) | Low-Moderate | Low (generator) |
| Efficiency | Good | Highest | High | Lower |
| Cost | Lower | Higher | Moderate | Lowest (gen only) |
| Rare-earth materials | No | Yes | Yes | No |
| Typical power class | 1.5-4 MW | 3-15+ MW | 4-15+ MW | 0.5-3 MW |

---

# Cac Loai May Phat Tuabin Gio

## Tong Quan

May phat la thanh phan chuyen doi nang luong co hoc quay cua rotor tuabin gio thanh nang luong dien. Viec lua chon loai may phat anh huong co ban den toan bo thiet ke he truyen dong, yeu cau dien tu cong suat, chien luoc ket noi luoi va hieu suat tong the cua tuabin. Ba loai may phat chinh thong tri nganh nang luong gio: May Phat Cam Ung Cap Nguon Kep (DFIG), May Phat Dong Bo Nam Cham Vinh Cuu (PMSG) va May Phat Cam Ung Roto Long Soc (SCIG).

## May Phat Cam Ung Cap Nguon Kep (DFIG)

### Nguyen Ly Hoat Dong

DFIG la may phat cam ung rotor day quon trong do ca cuon day stator va rotor deu hoat dong dien. Stator ket noi truc tiep voi luoi dien, trong khi rotor ket noi voi luoi thong qua bo bien doi cong suat mot phan (thuong dinh muc 25-30% cong suat dinh muc cua may phat).

### Dac Diem Chinh
- Pham vi toc do: +/- 30% quanh toc do dong bo
- Dinh muc bo bien doi: 25-30% cong suat dinh muc
- Hop so: Bat buoc (hop so ba cap la tieu chuan)
- Vong truot va choi than: Bat buoc (hang muc bao tri)

### Uu Diem
- Chi phi bo bien doi thap hon do dinh muc mot phan
- Cong nghe da duoc chung minh voi hang thap ky lich su van hanh
- Kha nang dieu khien cong suat phan khang tot

### Nhuoc Diem
- Yeu cau hop so nhieu cap (thanh phan bao tri va hu hong chinh)
- Vong truot va choi than can thay the dinh ky
- Kha nang vuot qua su co han che

## May Phat Dong Bo Nam Cham Vinh Cuu (PMSG)

### Nguyen Ly Hoat Dong

PMSG su dung nam cham vinh cuu (thuong la neodymium-sat-boron, NdFeB) gan tren rotor de tao truong tu, loai bo nhu cau kich tu dien cho rotor. Bo bien doi cong suat toan phan giua may phat va luoi chuyen doi dau ra tan so thay doi thanh tan so luoi.

### Cau Hinh

**PMSG Truyen Dong Truc Tiep:**
- May phat hoat dong o toc do rotor (8-20 RPM)
- May phat duong kinh rat lon (4-8 met) voi so cuc cao
- Khong co hop so, loai bo mot che do hu hong chinh

**PMSG Toc Do Trung Binh:**
- Hop so mot hoac hai cap (ty so truyen 1:10 den 1:40)
- May phat hoat dong o 100-400 RPM
- May phat nho hon truyen dong truc tiep, vo tuabin nhe hon

### Uu Diem
- Hieu suat cao hon toan dai hoat dong
- Khong co vong truot hoac choi than
- Pham vi toc do day du qua bo bien doi toan phan
- Kha nang vuot qua su co luoi vuot troi
- Cau hinh truyen dong truc tiep loai bo hu hong hop so

### Nhuoc Diem
- Bo bien doi toan phan dat hon
- Nam cham vinh cuu su dung vat lieu dat hiem voi lo ngai ve chuoi cung ung va bien dong gia
- May phat truyen dong truc tiep rat lon va nang
- Nguy co khu tu nam cham vinh cuu o nhiet do cao

## May Phat Cam Ung Roto Long Soc (SCIG)

### Nguyen Ly Hoat Dong

SCIG la loai may phat don gian nhat. No co stator voi cuon day ket noi luoi va rotor gom cac thanh nhom hoac dong ngan mach boi cac vong dau (giong long soc). Rotor khong co ket noi dien.

### Uu Diem
- Chi phi may phat thap nhat va cau tao don gian nhat
- Cuc ky ben voi yeu cau bao tri toi thieu
- Khong co vong truot, choi than, nam cham vinh cuu
- Khong co rui ro chuoi cung ung vat lieu dat hiem

### Nhuoc Diem
- Van hanh toc do co dinh han che thu nang luong
- Yeu cau bo bien doi toan phan cho van hanh toc do thay doi
- Hieu suat thap hon PMSG do ton that rotor

## Bang So Sanh

| Dac Diem | DFIG | PMSG Truc Tiep | PMSG Toc Do TB | SCIG |
|---|---|---|---|---|
| Bo bien doi | Mot phan (30%) | Toan phan (100%) | Toan phan (100%) | Khong hoac Toan phan |
| Hop so | 3 cap | Khong | 1-2 cap | 3 cap |
| Pham vi toc do | +/- 30% | Day du | Day du | Co dinh hoac Day du |
| Bao tri | Trung binh | Thap | Thap-TB | Thap (may phat) |
| Hieu suat | Tot | Cao nhat | Cao | Thap hon |
| Cong suat dien hinh | 1.5-4 MW | 3-15+ MW | 4-15+ MW | 0.5-3 MW |
