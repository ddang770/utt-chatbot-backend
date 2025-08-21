import os
import datetime

def format_size(size_bytes):
    """Chuyển byte → KB/MB/GB"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"

def get_document_file_metadata():
    folder_path = "data"
    files_info = []
    try:
        for f in os.listdir(folder_path):
            file_path = os.path.join(folder_path, f)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                upload_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d")
                file_type = os.path.splitext(f)[1].replace(".", "").upper()  # ví dụ ".pdf" → "PDF"
                
                info = {
                    "name": f,
                    "size": format_size(size),
                    "uploadDate": upload_date,
                    "status": "processed",
                    "type": file_type
                }
                files_info.append(info)

        #print(files_info)
        return  {
            "EC": 0,
            "EM": "Get document metadata success",
            "DT": files_info
        }
    except Exception as e:
        print(f"Error: {str(e)}")  # In ra lỗi để debug
        return  {
            "EC": 1,
            "EM": "Something wrong in service...",
            "DT": []
        }