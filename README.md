# SSF × XD Dashboard บน GitHub (ไม่ต้องใช้เทอร์มินัล)

GitHub รันสคริปต์ให้ทุก ~15 นาที: เรียก SET API -> สะสมประวัติ -> เผยแพร่เป็นหน้าเว็บ (GitHub Pages)

## ตั้งค่าครั้งเดียว (ทำบนเว็บ GitHub ทั้งหมด)
1. สร้าง repository ใหม่ (New repository) ตั้งเป็น **Public** (Pages ของ repo ส่วนตัวต้องใช้แพ็กเกจเสียเงิน)
   - Public หมายถึงโค้ด ssf_list.txt และ data/set_ca.csv ใครก็เปิดดูได้ แต่ API key ไม่หลุด เพราะเก็บใน Secrets
2. อัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ (Add file > Upload files ลากทั้งโฟลเดอร์ แล้ว Commit)
   - โฟลเดอร์ `.github` เป็นโฟลเดอร์ซ่อน อาจไม่ถูกลากมาด้วย ถ้าแท็บ Code ไม่เห็น `.github/workflows/update.yml`
     ให้กด Add file > Create new file พิมพ์ชื่อ `.github/workflows/update.yml` แล้ววางเนื้อหาจากไฟล์เดิม
3. Settings > Secrets and variables > Actions > New repository secret
   - Name: `SET_API_KEY`  Value: API key จริงของคุณ
4. Settings > Pages > Build and deployment > Source เลือก **GitHub Actions**
5. แท็บ Actions > update-dashboard > Run workflow รอจนขึ้นเขียว
   ลิงก์เว็บจะอยู่ที่ `https://<ชื่อ GitHub>.github.io/<ชื่อ repo>/` (ดูได้ในผลการรันที่ขั้น deploy)
6. เปิดไฟล์ `ssf_list.txt` กดรูปดินสอ ใส่ชื่อหุ้นที่มี SSF แล้ว Commit (เว็บจะสร้างใหม่เอง)

## ถ้าผิดพลาด
- แท็บ Actions: รอบที่เป็นสีแดง กดดูข้อความ error
  - `HTTP 401/403` = key ผิดหรือไม่มีสิทธิ์ ตรวจที่ Secret และหน้า API Key ของ SET
  - `ไม่พบ SET_API_KEY` = ชื่อ Secret ต้องเป็น SET_API_KEY ตัวพิมพ์ใหญ่ตรงตัว
- ถ้ารอบล้มเหลว เว็บจะคงข้อมูลชุดก่อนหน้าไว้
- GitHub อาจหน่วงรอบ schedule และอาจปิด schedule อัตโนมัติถ้า repo เงียบนาน ถ้าเจอให้กด Enable ที่แท็บ Actions

## หมายเหตุ
- ปันผลพิเศษ: API ไม่มีฟิลด์นี้ ถ้าหุ้นเดียวกันมี CD หลายแถวในวัน XD/วันประกาศเดียวกัน แถวแรก = ปันผล ที่เหลือ = EXTRA (เดา ตรวจกับข่าวจริง)
- ประวัติสะสมอยู่ที่ `data/set_ca.csv` (สคริปต์ commit ให้เองเมื่อมีการเปลี่ยนแปลง)
