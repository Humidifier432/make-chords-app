from flask import Flask, request, render_template, send_file
import os
import shutil
import zipfile
from make_music_chords import generate_music

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("chord_selector.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    chord_data = data.get("chord_data", "")

    # 保存用フォルダの作成
    upload_folder = "uploads"
    output_folder = "outputs"
    zip_path = "outputs/output_bundle.zip"

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # ① 以前のMIDIファイルを削除（outputs 内を空にする）
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path) and file_path.endswith(".mid"):
            os.remove(file_path)

    # テキストファイル保存
    input_txt = os.path.join(upload_folder, "selected_chords.txt")
    with open(input_txt, "w", encoding="utf-8") as f:
        f.write(chord_data)

    # MIDIファイルの生成
    generate_music(
        filename=input_txt,
        input_folder=os.path.join("uploads", "chords"),
        output_folder=output_folder
    )

    # 古いZIPファイル削除
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # output_folder 内の全MIDIファイルをZIPにまとめる
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                if file.endswith(".mid"):
                    filepath = os.path.join(root, file)
                    zipf.write(filepath, arcname=file)

    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
