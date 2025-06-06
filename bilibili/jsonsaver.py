import os
import json

# JsonSaver 类的定义
class JsonSaver:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_to_json(self, data, filename="output.json", append=False):
        file_path = os.path.join(self.output_dir, filename)
        final_data = data

        if append and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, list) and isinstance(data, list):
                    final_data = existing_data + data
                    print(f"检测到现有数据，追加 {len(data)} 条新数据。")
                elif isinstance(existing_data, dict) and isinstance(data, dict):
                    final_data = {**existing_data, **data}
                    print(f"检测到现有数据，合并新数据。")
                else:
                    print("现有文件格式与要追加的数据格式不匹配，将覆盖写入。")
                    final_data = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"读取现有文件失败或格式错误: {e}，将直接覆盖写入。")
                final_data = data
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"数据已成功保存到文件: {file_path}")
            return True
        except IOError as e:
            print(f"写入文件失败: {e}")
            return False