def read_html_template(file_path):
    """
    讀取 HTML 模板文件並返回其完整內容為字串
    
    Args:
        file_path (str): HTML 模板文件的路徑
        
    Returns:
        str: 包含所有文字（含換行）的字串
        
    Raises:
        FileNotFoundError: 如果指定的文件不存在
        IOError: 如果讀取文件時發生錯誤
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        return template_content
    except FileNotFoundError:
        raise FileNotFoundError(f"模板文件不存在: {file_path}")
    except IOError as e:
        raise IOError(f"讀取模板文件時發生錯誤: {str(e)}")
    
def read_js_file(file_path):
    """
    讀取 JavaScript 檔案並返回其完整內容為字串
    
    Args:
        file_path (str): JavaScript 檔案的路徑
        
    Returns:
        str: 包含所有文字（含換行）的字串
        
    Raises:
        FileNotFoundError: 如果指定的檔案不存在
        IOError: 如果讀取檔案時發生錯誤
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            js_content = file.read()
        return js_content
    except FileNotFoundError:
        raise FileNotFoundError(f"JavaScript 檔案不存在: {file_path}")
    except IOError as e:
        raise IOError(f"讀取 JavaScript 檔案時發生錯誤: {str(e)}")