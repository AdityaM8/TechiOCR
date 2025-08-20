import os, io, zipfile, tempfile, shutil
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import pytesseract
from googletrans import Translator
import platform
from gtts import gTTS

# ---------- App & Theme ----------
st.set_page_config(page_title="OCR Studio", page_icon="🧠", layout="wide")

# Tesseract path (adjust if needed)
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    # Streamlit Cloud (Linux)
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# ---------- Session State ----------
for key, default in {
    "images_text": {},          # {filename: text}
    "combined_text": "",
    "translated_text": "",
    "last_audio_path": "",
    "search_term": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Sidebar ----------
with st.sidebar:
    st.title("⚙️ Settings")

    # Language choices
    LANGUAGES = {
        "Hindi": "hi", "French": "fr", "German": "de", "Spanish": "es",
        "Chinese (Simplified)": "zh-cn", "Arabic": "ar", "Japanese": "ja",
        "Russian": "ru", "Bengali": "bn", "Urdu": "ur", "English": "en"
    }
    target_lang_name = st.selectbox("🌐 Translate to", list(LANGUAGES.keys()), index=0)
    target_lang_code = LANGUAGES[target_lang_name]

    st.markdown("**OCR Options**")
    oem = st.selectbox("OCR Engine Mode (--oem)", ["3 (Default)", "1 (Neural LSTM)", "0 (Legacy)"], index=0)
    psm = st.selectbox("Page Segmentation Mode (--psm)", [
        "6 (Block of text)", "3 (Fully automatic)", "4 (Single column)", "7 (Single line)"
    ], index=0)

    oem_val = {"3 (Default)": 3, "1 (Neural LSTM)": 1, "0 (Legacy)": 0}[oem]
    psm_val = {"6 (Block of text)": 6, "3 (Fully automatic)": 3, "4 (Single column)": 4, "7 (Single line)": 7}[psm]
    tess_config = f"--oem {oem_val} --psm {psm_val}"

    st.markdown("---")
    st.caption("Tip: For scanned book pages, try PSM 4 or 6. For a single line, try PSM 7.")

# ---------- Header ----------
st.title("🧠 OCR Studio — Extract • Translate • Listen")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload", "📝 Extracted", "🌍 Translate", "🔊 Audio", "📚 History"])

with tab1:
    st.subheader("Upload Images or a ZIP of Images")
    colA, colB = st.columns(2)
    with colA:
        img_files = st.file_uploader("Upload image(s)", type=["png", "jpg", "jpeg", "tif", "tiff"], accept_multiple_files=True)
    with colB:
        zip_file = st.file_uploader("…or upload a ZIP", type=["zip"])

    run_ocr = st.button("🚀 Run OCR")
    if run_ocr:
        st.session_state.images_text.clear()
        st.session_state.combined_text = ""
        with st.status("Processing images…", expanded=True) as status:
            temp_dir = None

            # Collect file-like objects to process
            to_process = []
            if img_files:
                for f in img_files:
                    to_process.append((f.name, Image.open(f)))
                    st.write(f"queued: {f.name}")

            if zip_file:
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(zip_file, "r") as z:
                    z.extractall(temp_dir)
                for name in os.listdir(temp_dir):
                    if name.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
                        path = os.path.join(temp_dir, name)
                        to_process.append((name, Image.open(path)))
                        st.write(f"queued (zip): {name}")

            # Process
            for fname, pil_img in to_process:
                # Preprocess with OpenCV
                img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                text = pytesseract.image_to_string(thr, config=tess_config)

                st.session_state.images_text[fname] = text
                st.session_state.combined_text += f"\n--- {fname} ---\n{text.strip()}\n"
                st.write(f"✅ processed: {fname} (chars: {len(text)})")

            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

            if st.session_state.combined_text.strip():
                status.update(label="Done!", state="complete")
                st.toast("OCR complete.", icon="✅")
            else:
                status.update(label="No text found.", state="error")
                st.toast("No extractable text.", icon="⚠️")

with tab2:
    st.subheader("Extracted Text")
    st.write("Combined from all processed images.")
    st.session_state.search_term = st.text_input("🔎 Search within text", value=st.session_state.get("search_term", ""))

    display_text = st.session_state.combined_text
    if st.session_state.search_term:
        # Simple highlight: wrap matches in **bold**
        term = st.session_state.search_term
        display_text = display_text.replace(term, f"**{term}**")

    st.text_area("OCR Output", display_text, height=320)

    if st.session_state.combined_text.strip():
        st.download_button(
            "⬇️ Download OCR Text",
            data=st.session_state.combined_text.encode("utf-8"),
            file_name="ocr_output.txt",
            mime="text/plain",
        )

    if st.session_state.images_text:
        st.caption("Per-image results:")
        for fname, txt in st.session_state.images_text.items():
            with st.expander(fname):
                st.code(txt or "(no text)")

with tab3:
    st.subheader("Translate")
    if st.button("🌍 Translate Text"):
        if st.session_state.combined_text.strip():
            try:
                translator = Translator()
                translated = translator.translate(st.session_state.combined_text, dest=target_lang_code).text
                st.session_state.translated_text = translated
                st.success("Translated!")
            except Exception as e:
                st.error(f"Translation failed: {e}")
        else:
            st.warning("No text to translate. Run OCR first.")

    st.text_area("Translated Text", st.session_state.translated_text, height=320)
    if st.session_state.translated_text.strip():
        st.download_button(
            "⬇️ Download Translated Text",
            data=st.session_state.translated_text.encode("utf-8"),
            file_name=f"translated_{target_lang_code}.txt",
            mime="text/plain",
        )

with tab4:
    st.subheader("Text-to-Speech")
    if st.button("🔊 Generate Speech"):
        text_to_speak = st.session_state.translated_text or st.session_state.combined_text
        if text_to_speak.strip():
            try:
                tts = gTTS(text_to_speak, lang=target_lang_code)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.session_state.last_audio_path = fp.name
                st.success("Audio ready!")
            except Exception as e:
                st.error(f"TTS failed: {e}")
        else:
            st.warning("Nothing to speak. Translate or extract text first.")

    if st.session_state.last_audio_path and os.path.exists(st.session_state.last_audio_path):
        with open(st.session_state.last_audio_path, "rb") as af:
            audio_bytes = af.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("⬇️ Download Audio", data=audio_bytes, file_name="speech.mp3", mime="audio/mpeg")

with tab5:
    st.subheader("Run History (this session)")
    st.write(f"🖼️ Images processed: {len(st.session_state.images_text)}")
    st.write(f"✍️ OCR characters: {len(st.session_state.combined_text)}")
    st.write(f"🌐 Current target language: **{target_lang_name}** (`{target_lang_code}`)")

