.venv\Scripts\python.exe mdcrawler.py^
 -i "C:\\Daten\Dokumente\\workcopies_mafi\\Produktlinien"^
 -i "C:\\Data\gitlab\inhouse"^
 -x ".venv"^
 -x "mistletoe"^
 -x "kiwi"^
 -o result.json
 cscript send_outlookmail.vbs %~dp0\result.json