import streamlit as st
import os
import yaml
from pathlib import Path

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_supported_files(directory, supported_types):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in supported_types):
                # Get relative path from input directory
                rel_path = os.path.relpath(os.path.join(root, filename), directory)
                files.append(rel_path)
    return sorted(files)

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {str(e)}")
        return ""

def split_into_paragraphs(text):
    # Split text into paragraphs (separated by one or more blank lines)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs

st.set_page_config(
    page_title="مراجعة الترجمة",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'delete_after_translation' not in st.session_state:
    st.session_state.delete_after_translation = False
if 'translated_paragraphs' not in st.session_state:
    st.session_state.translated_paragraphs = []
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

def add_paragraph_after(index):
    st.session_state.translated_paragraphs.insert(index + 1, "")

def delete_paragraph(index):
    if len(st.session_state.translated_paragraphs) > 0:
        st.session_state.translated_paragraphs.pop(index)

st.title("مراجعة وتحرير الترجمة 📝")
st.markdown("---")

# Add settings to the sidebar
with st.sidebar:
    st.header("الإعدادات ⚙️")
    st.session_state.delete_after_translation = st.checkbox(
        "حذف الملفات الأصلية بعد الترجمة",
        value=st.session_state.delete_after_translation,
        help="عند تفعيل هذا الخيار، سيتم حذف الملف الأصلي بعد حفظ الترجمة"
    )

try:
    config = load_config()
    input_dir = config['input_directory']
    output_dir = config['output_directory']
    supported_types = config['supported_file_types']

    # File selection
    input_files = get_supported_files(input_dir, supported_types)
    if not input_files:
        st.error(f"لا توجد ملفات مدعومة في مجلد المدخلات. الأنواع المدعومة: {', '.join(supported_types)}")
        st.info("يمكنك إضافة ملفات جديدة عن طريق صفحة 'رفع الملفات' 📤")
    else:
        selected_file = st.selectbox(
            "اختر الملف للمراجعة",
            input_files,
            format_func=lambda x: f"{x} ({os.path.splitext(x)[1]})"
        )

        if selected_file:
            # Read source and translated files
            source_path = os.path.join(input_dir, selected_file)
            translated_path = os.path.join(output_dir, selected_file)

            # Create output directory structure if it doesn't exist
            os.makedirs(os.path.dirname(translated_path), exist_ok=True)

            if not os.path.exists(translated_path):
                st.warning("الملف المترجم غير موجود. سيتم إنشاؤه عند الحفظ.")
                translated_text = ""
            else:
                translated_text = read_file(translated_path)

            source_text = read_file(source_path)

            # Add file info
            st.info(f"""معلومات الملف ℹ️:
            - المسار: {selected_file}
            - النوع: {os.path.splitext(selected_file)[1]}
            - الحجم: {os.path.getsize(source_path) / 1024:.1f} KB""")

            # Split both texts into paragraphs
            source_paragraphs = split_into_paragraphs(source_text)
            
            # Initialize or update translated paragraphs if file changed
            if st.session_state.current_file != selected_file:
                st.session_state.current_file = selected_file
                st.session_state.translated_paragraphs = split_into_paragraphs(translated_text)

            # Create two columns
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("النص الأصلي 📄")
            with col2:
                st.subheader("النص المترجم 🔄")

            # Controls for managing paragraphs
            cols = st.columns([0.8, 0.2])
            with cols[1]:
                if st.button("➕ إضافة فقرة جديدة", key="add_final"):
                    add_paragraph_after(len(st.session_state.translated_paragraphs) - 1)
                    st.rerun()

            # Display paragraphs
            for i, source in enumerate(source_paragraphs):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Display source text (read-only)
                    st.text_area(
                        f"النص الأصلي {i+1}",
                        value=source,
                        height=150,
                        disabled=True,
                        key=f"source_{i}"
                    )
                
                with col2:
                    # Controls for current paragraph
                    control_cols = st.columns([0.7, 0.15, 0.15])
                    with control_cols[1]:
                        if st.button("➕", key=f"add_{i}"):
                            add_paragraph_after(i)
                            st.rerun()
                    with control_cols[2]:
                        if st.button("❌", key=f"delete_{i}"):
                            delete_paragraph(i)
                            st.rerun()
                    
                    # Display translated text if available
                    if i < len(st.session_state.translated_paragraphs):
                        edited = st.text_area(
                            f"الترجمة {i+1}",
                            value=st.session_state.translated_paragraphs[i],
                            height=150,
                            key=f"translated_{i}"
                        )
                        st.session_state.translated_paragraphs[i] = edited

            # Create a form for saving changes
            with st.form("save_changes"):
                if st.form_submit_button("💾 حفظ التغييرات", use_container_width=True):
                    # Join the edited paragraphs with double newlines
                    final_text = '\n\n'.join(st.session_state.translated_paragraphs)
                    
                    # Save the edited translation
                    try:
                        with open(translated_path, 'w', encoding='utf-8') as f:
                            f.write(final_text)
                        
                        # Delete original file if option is selected
                        if st.session_state.delete_after_translation:
                            try:
                                os.remove(source_path)
                                st.success(f"✅ تم حفظ الترجمة وحذف الملف الأصلي بنجاح!")
                                # Rerun the app to update the file list
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ تم حفظ الترجمة ولكن حدث خطأ أثناء حذف الملف الأصلي: {str(e)}")
                        else:
                            st.success("✅ تم حفظ التغييرات بنجاح!")
                    except Exception as e:
                        st.error(f"❌ خطأ في حفظ الملف: {str(e)}")

except Exception as e:
    st.error(f"❌ حدث خطأ: {str(e)}")
    st.info("تأكد من وجود ملف config.yaml في المجلد الرئيسي للتطبيق")
