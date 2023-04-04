import atexit
import pypinyin as pinyin
import re
import customtkinter as tk
import json
import opencc
import unicodedata
from PIL import Image


# main process
class ChineseToPinyin:
    __instance = None
    __inited = False

    # Singleton
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if not self.__inited:
            self.config_json_data = None
            self.show_information_log = False
            self.space_after_pinyin = False
            self.convert_type = 0
            self.appearance_mode = 2
            self.initial_config_special_pinyin()
            self.__inited = True
        return

    def update_config(self):
        self.config_json_data["showInfo"] = self.show_information_log
        self.config_json_data["spaceAfterPinyin"] = self.space_after_pinyin
        self.config_json_data["convertType"] = self.convert_type
        self.config_json_data["appearanceMode"] = self.appearance_mode
        with open("./config.json", "w", encoding="utf8") as config_file:
            if self.show_information_log:
                print("Rewrite back to json config file: {}".format(self.config_json_data))
            json.dump(self.config_json_data, config_file, indent=2, ensure_ascii=False)

    def initial_config_special_pinyin(self):
        """
        Load special pinyin from config.json
        it will load single character and phrases
        if the word is simplified and different from traditional, it will load both
        """
        with open("./config.json", "r", encoding='utf8') as file:
            self.config_json_data = json.load(file)

        self.show_information_log = self.config_json_data["showInfo"]
        self.space_after_pinyin = self.config_json_data["spaceAfterPinyin"]
        self.convert_type = self.config_json_data["convertType"]
        self.appearance_mode = self.config_json_data["appearanceMode"]
        tk.set_appearance_mode(
            self.config_json_data["commentAppearanceModeList"][self.config_json_data["appearanceMode"]]["name"])

        if type(self.config_json_data["specialWord"]) == list and len(self.config_json_data["specialWord"]) > 0:
            for i in self.config_json_data["specialWord"]:
                if self.to_simplified(i["word"]) != self.to_traditional(i["word"]):
                    self.load_dict_word(self.to_simplified(i["word"]), i["pinyin"])
                    self.load_dict_word(self.to_traditional(i["word"]), i["pinyin"])
                else:
                    self.load_dict_word(i["word"], i["pinyin"])
        pass

    def load_dict_word(self, json_word, json_pinyin):
        if len(json_word) == 1:
            pinyin.load_single_dict({ord(json_word): json_pinyin})
            if self.show_information_log:
                print(f"Loaded {json_word} with pinyin {json_pinyin}")
        elif len(json_word) > 1:
            pinyin_data = list(map(lambda x: [x], json_pinyin.split(" ")))
            pinyin.load_phrases_dict({json_word: pinyin_data})
            if self.show_information_log:
                print(f"Loaded {json_word} with pinyin {pinyin_data}")
        else:
            pass

    @staticmethod
    def to_simplified(text):
        # convert traditional to simplified
        return opencc.OpenCC('t2s.json').convert(text)

    @staticmethod
    def to_traditional(text):
        # convert simplified to traditional
        return opencc.OpenCC('s2t.json').convert(text)

    @staticmethod
    def cjk_detect(texts):
        # korean
        if re.search("[\uac00-\ud7a3]", texts):
            return "ko"
        # japanese
        if re.search("[\u3040-\u30ff]", texts):
            return "ja"
        # chinese
        if re.search("[\u4e00-\u9fff]", texts):
            return "zh"
        return None

    def convert_to_pinyin(self, chinese_word):
        converted_pinyin = pinyin.lazy_pinyin(chinese_word, style=pinyin.Style.NORMAL)

        converted_pinyin[0] = converted_pinyin[0].capitalize()
        if self.show_information_log:
            print("Converted pinyin: {}".format(converted_pinyin))
        return (" ".join(converted_pinyin)).replace('  ', ' ')

    def main_convert_from_app(self, list_data):
        output = []
        for i in range(len(list_data)):
            if self.show_information_log:
                print("第{}段：{}".format(i + 1, list_data[i]))
            if self.cjk_detect(list_data[i]) == 'zh':
                if self.convert_type == 1:
                    output.append(self.to_simplified(list_data[i]))
                elif self.convert_type == 2:
                    output.append(self.to_traditional(list_data[i]))
                else:
                    output.append(list_data[i])
                output.append(self.convert_to_pinyin(list_data[i]))
                if self.space_after_pinyin and list_data[i] != list_data[len(list_data) - 1] and len(
                        list_data[i + 1]) != 0:
                    output.append("\n")
            else:
                output.append("\n") if len(list_data[i]) == 0 else output.append(list_data[i])
        if len(output) > 0:
            return output

    def main_reading_from_text(self):
        try:
            output = []
            for i in self.text_reading():
                # print("\n") if len(i) == 0 else print(i)
                output.append("\n") if len(i) == 0 else output.append(i)
                if self.cjk_detect(i) == 'zh':
                    # print(convert_to_pinyin(i))
                    output.append(self.convert_to_pinyin(i))
            if len(output) > 0:
                self.text_output(output)

        except Exception as e:
            print(e)

    @staticmethod
    def text_reading():
        with open("./input.txt", 'r', encoding='utf8') as f:
            list_a = []
            for item in f.readlines():
                list_a.append(unicodedata.normalize("NFKC", item.strip()))
            # print(list_a)
            return list_a

    @staticmethod
    def text_output(output):
        with open("./output.txt", "w", encoding='utf8') as file:
            for b in range(len(output)):
                if output[b] == "\n":
                    file.write("\n")
                else:
                    file.write(output[b] + "\n")


# setting window
class SettingWindow(tk.CTkToplevel):
    def __init__(self, default_font_size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x500+{}+{}".format(int(self.winfo_screenwidth() / 2 - 150),
                                             int(self.winfo_screenheight() / 2 - 150 - 100)))
        self.minsize(400, 500)
        # self.maxsize(400, 500)
        self.title("Setting")
        self.default_font_size = default_font_size
        self.chineseToPinyin = ChineseToPinyin()

        # convert type
        self.auto_convert_type_label = tk.CTkLabel(self, text="Auto Convert Type:", anchor="w",
                                                   font=self.default_font_size)
        self.auto_convert_type_label.pack(padx=20, pady=(20, 0))
        self.auto_convert_type_values = ["No Convert", "Convert to Simplified Chinese",
                                         "Convert to Traditional Chinese"]
        self.auto_convert_type = tk.CTkOptionMenu(self, command=self.auto_convert_type_event,
                                                  values=self.auto_convert_type_values,
                                                  font=self.default_font_size, dropdown_font=self.default_font_size,
                                                  height=35, anchor="center")
        self.auto_convert_type.pack(padx=20, pady=20)

        # show log
        self.show_log_label = tk.CTkLabel(self, text="Show Log Info:", anchor="center",
                                          font=self.default_font_size)
        self.show_log_label.pack(padx=20, pady=(20, 0))
        self.show_log = tk.CTkSwitch(master=self, text="Off / On", font=self.default_font_size,
                                     command=self.show_log_event)
        self.show_log.pack(padx=20, pady=20)

        # space after pinyin
        self.space_after_pinyin_label = tk.CTkLabel(self, text="Auto Spacing After Pinyin:", anchor="center",
                                                    font=self.default_font_size)
        self.space_after_pinyin_label.pack(padx=20, pady=(20, 0))
        self.space_after_pinyin = tk.CTkSwitch(master=self, text="Off / On", font=self.default_font_size,
                                               command=self.space_after_pinyin_event)
        self.space_after_pinyin.pack(padx=20, pady=20)

        # appearance mode
        self.appearance_mode_label = tk.CTkLabel(self, text="Appearance Mode:", anchor="w",
                                                 font=self.default_font_size)
        self.appearance_mode_label.pack(padx=20, pady=(20, 0))
        self.appearance_mode_option_values = ["System", "Light", "Dark"]
        self.appearance_mode_option_menu = tk.CTkOptionMenu(self, values=self.appearance_mode_option_values,
                                                            command=self.change_appearance_mode_event,
                                                            font=self.default_font_size,
                                                            dropdown_font=self.default_font_size, height=35,
                                                            anchor="center")
        self.appearance_mode_option_menu.pack(padx=20, pady=20)

        # set default value
        self.appearance_mode_option_menu.set(self.appearance_mode_option_values[self.chineseToPinyin.appearance_mode])
        self.auto_convert_type.set(self.auto_convert_type_values[self.chineseToPinyin.convert_type])
        self.show_log.select() if self.chineseToPinyin.show_information_log else self.show_log.deselect()
        self.space_after_pinyin.select() if self.chineseToPinyin.space_after_pinyin else self.space_after_pinyin.deselect()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        if new_appearance_mode in self.appearance_mode_option_values:
            tk.set_appearance_mode(new_appearance_mode)
            self.chineseToPinyin.appearance_mode = self.appearance_mode_option_values.index(new_appearance_mode)
            self.after(100, self.focus)
        else:
            pass

    def auto_convert_type_event(self, value):
        if value in self.auto_convert_type_values:
            self.chineseToPinyin.convert_type = self.auto_convert_type_values.index(value)
        else:
            pass

    def show_log_event(self):
        if self.show_log.get() > 0:
            self.chineseToPinyin.show_information_log = True
        else:
            self.chineseToPinyin.show_information_log = False
        pass

    def space_after_pinyin_event(self):
        if self.space_after_pinyin.get() > 0:
            self.chineseToPinyin.space_after_pinyin = True
        else:
            self.chineseToPinyin.space_after_pinyin = False
        pass


# main window
class App(tk.CTk):
    def __init__(self):
        super().__init__()
        self.chineseToPinyin = ChineseToPinyin()
        self.geometry(
            f"{1100}x{580}+{int(self.winfo_screenwidth() / 2 - 550)}+{int(self.winfo_screenheight() / 2 - 290)}")
        self.title("Chinese to Pinyin Converter")
        self.minsize(800, 500)
        # create 4x4 grid system
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.default_font_size = tk.CTkFont(size=18)

        # create labels
        self.label_input = tk.CTkLabel(master=self, text="Input", font=tk.CTkFont(size=24),
                                       height=10, justify="center")
        self.label_input.grid(row=0, column=0, padx=20, pady=(20, 0), columnspan=2, sticky="ESW")
        self.label_output = tk.CTkLabel(master=self, text="Output", font=tk.CTkFont(size=24),
                                        height=10, justify="center")
        self.label_output.grid(row=0, column=2, padx=20, pady=(20, 0), sticky="ESW", columnspan=2)
        self.button_setting = tk.CTkButton(master=self, command=self.button_setting_callback, text="",
                                           height=40, width=50, font=self.default_font_size,
                                           image=tk.CTkImage(light_image=Image.open("./setting-icon-png-8.jpg"),
                                                             dark_image=Image.open("./setting-icon-png-8.jpg"),
                                                             size=(30, 30)))
        self.button_setting.grid(row=0, column=3, padx=20, pady=(20, 0), sticky="SE")

        # create input textbox
        self.input_textbox = tk.CTkTextbox(master=self, width=250, font=self.default_font_size)
        self.input_textbox.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="NSEW")
        # create output textbox
        self.output_textbox = tk.CTkTextbox(master=self, width=250, font=self.default_font_size, state=tk.DISABLED)
        self.output_textbox.grid(row=1, column=2, padx=20, columnspan=2, pady=20, sticky="NSEW")

        # create button to convert
        self.button_reset = tk.CTkButton(master=self, command=self.button_reset_callback, text="Reset",
                                         font=self.default_font_size, height=40)
        self.button_reset.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="w")
        self.button_convert = tk.CTkButton(master=self, command=self.button_callback, text="Convert",
                                           font=self.default_font_size, height=40, width=600)
        self.button_convert.grid(row=2, column=1, columnspan=2, padx=20, pady=(10, 20), sticky="")
        self.button_exit = tk.CTkButton(master=self, command=self.button_exit_callback, text="Exit",
                                        font=self.default_font_size, height=40)
        self.button_exit.grid(row=2, column=3, padx=20, pady=(10, 20), sticky="e")

        self.setting_window = None

    def button_setting_callback(self):
        # open new setting window in tk
        if self.setting_window is None or not self.setting_window.winfo_exists():
            self.setting_window = SettingWindow(self.default_font_size, self)  # create window if its None or destroyed
            self.setting_window.after(30, self.setting_window.lift)
            self.setting_window.after(30, self.setting_window.focus)
        else:
            if self.setting_window.state() == "iconic":
                self.setting_window.deiconify()  # if window is minimized, restore it
            self.setting_window.focus()  # if window exists focus it

        return None

    def button_callback(self):
        # get input from textbox and convert it to list
        a = self.input_textbox.get("1.0", "end-1c")
        a = unicodedata.normalize("NFKC", a).split('\n')
        # convert each line to pinyin
        output = self.chineseToPinyin.main_convert_from_app(a)
        self.output_textbox.configure(state=tk.NORMAL)
        self.output_textbox.delete("0.0", "end")
        for b in range(len(output)):
            if output[b] == "\n":
                self.output_textbox.insert("insert", "\n")
            else:
                self.output_textbox.insert("insert", output[b] + "\n")
        self.output_textbox.configure(state=tk.DISABLED)

    def button_reset_callback(self):
        self.input_textbox.delete("0.0", "end")
        self.output_textbox.configure(state=tk.NORMAL)
        self.output_textbox.delete("0.0", "end")
        self.output_textbox.configure(state=tk.DISABLED)

    def button_exit_callback(self):
        self.destroy()


@atexit.register
def exit_main():
    chinese_to_pinyin_main_call = ChineseToPinyin()
    chinese_to_pinyin_main_call.update_config()
    if chinese_to_pinyin_main_call.config_json_data["showInfo"]:
        print("Exit")


def main():
    try:
        tk.set_default_color_theme("blue")
        App().mainloop()

    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
