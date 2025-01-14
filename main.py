import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import os
import json
from PIL import Image, ImageTk


def clear_images_folder(output_folder):
    """Önceden mevcut olan resimleri siler."""
    if os.path.exists(output_folder):
        for file in os.listdir(output_folder):
            file_path = os.path.join(output_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)


def extract_text_and_images_from_pdf(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    text_data = {}
    images_data = {}

    # Resimlerin bulunduğu klasörü temizle
    clear_images_folder(output_folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for page_number, page in enumerate(doc):
        page_text = page.get_text()
        text_data[f"page_{page_number + 1}"] = page_text.strip()

        # Resimleri çıkarma
        image_list = page.get_images(full=True)
        images_data[f"page_{page_number + 1}"] = []

        for img_index, img in enumerate(image_list):
            xref = img[0]
            image = doc.extract_image(xref)
            image_bytes = image["image"]

            # Resmi kaydetme
            image_filename = f"{output_folder}/page_{page_number + 1}_img_{img_index + 1}.png"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            images_data[f"page_{page_number + 1}"].append(image_filename)

    return text_data, images_data


def save_to_json(text_data, images_data, output_file):
    # JSON verisini hazırlıyoruz
    output_data = {
        "text": text_data,
        "images": images_data
    }

    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(output_data, json_file, ensure_ascii=False, indent=4)

    print(f"Metin ve resimler JSON dosyasına kaydedildi: {output_file}")


def select_pdf_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        pdf_file_entry.delete(0, tk.END)  # Önceki dosya adını temizle
        pdf_file_entry.insert(0, file_path)  # Yeni dosya yolunu ekle


def start_processing():
    pdf_path = pdf_file_entry.get()
    if not pdf_path:
        messagebox.showerror("Hata", "Lütfen bir PDF dosyası seçin.")
        return

    output_folder = "images"
    output_json = "output.json"

    # Başlık kısmını güncelleyelim
    root.title("PDF işlemesi başlatıldı... Yükleniyor...")

    # PDF'den metin ve resimleri çıkarma
    text_data, images_data = extract_text_and_images_from_pdf(pdf_path, output_folder)

    if text_data or images_data:
        save_to_json(text_data, images_data, output_json)
        display_json(output_json)  # JSON'ı ekranda göster
        display_images(images_data)  # Resimleri listele

        # Başlık kısmını işlem tamamlandı olarak güncelle
        root.title("PDF'den Metin ve Resim Çıkarma")
    else:
        messagebox.showerror("Hata", "PDF'den metin veya resim çıkarılamadı.")
        # Başlık kısmını hata mesajıyla güncelle
        root.title("PDF İşleme Hatası!")


def display_json(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        json_content = json.load(file)

    # JSON verisini Text widget'ında göster
    json_text.config(state=tk.NORMAL)  # Text widget'ını düzenlenebilir yap
    json_text.delete(1.0, tk.END)  # Önceki içeriği temizle
    json_text.insert(tk.END, json.dumps(json_content, ensure_ascii=False, indent=4))  # JSON'ı ekle
    json_text.config(state=tk.DISABLED)  # Text widget'ını sadece görüntülenebilir yap


def display_images(images_data):
    # Resimleri önizleme olarak gösterecek widget'ları temizle
    for widget in image_frame.winfo_children():
        widget.destroy()

    # Resim dosyalarının her birini aç ve Tkinter için uygun formatta göster
    for page, images in images_data.items():
        for image_path in images:
            img = Image.open(image_path)
            img.thumbnail((100, 100))  # Küçük önizleme boyutu
            img_tk = ImageTk.PhotoImage(img)

            # Resim öngörünümünü gösterecek Label widget'ı
            label = tk.Label(image_frame, image=img_tk)
            label.image = img_tk  # Referansı sakla
            label.pack(side=tk.LEFT, padx=5, pady=5)

            # İndir butonunu ekleyelim
            download_button = tk.Button(image_frame, text="İndir", command=lambda path=image_path: download_image(path))
            download_button.pack(side=tk.LEFT, padx=5)


def download_image(image_path):
    # Resmi kaydetmek için dosya kaydetme penceresini açıyoruz
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
    if save_path:
        try:
            img = Image.open(image_path)
            img.save(save_path)
            messagebox.showinfo("Başarı", f"Resim başarıyla kaydedildi: {save_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Resim kaydedilemedi: {e}")


def copy_json_to_clipboard():
    # JSON verisini kopyalamak için
    json_content = json_text.get(1.0, tk.END)
    root.clipboard_clear()  # Önceki kopyalanan veriyi temizle
    root.clipboard_append(json_content.strip())  # Yeni JSON verisini kopyala

    # Kopyalama işlemi başarılı olduğunda bilgi mesajını ekleyelim
    copied_label.config(text="Panoya kopyalandı", fg="green")


# Tkinter arayüzü oluşturma
root = tk.Tk()
root.title("PDF'den Metin ve Resim Çıkarma")
root.geometry("600x800")

# PDF dosyasını seçme butonu ve dosya yolu
pdf_file_label = tk.Label(root, text="PDF Dosyasını Seçin:")
pdf_file_label.pack(pady=10)

pdf_file_entry = tk.Entry(root, width=40)
pdf_file_entry.pack(pady=5)

select_button = tk.Button(root, text="Dosya Seç", command=select_pdf_file)
select_button.pack(pady=5)

# Başlat butonu
process_button = tk.Button(root, text="İşlemi Başlat", command=start_processing)
process_button.pack(pady=20)

# JSON verisini gösterecek Text widget
json_text = tk.Text(root, width=70, height=30)
json_text.pack(pady=10)

# JSON'ı kopyalamak için buton
copy_button = tk.Button(root, text="JSON'ı Kopyala", command=copy_json_to_clipboard)
copy_button.pack(pady=5)

# Kopyalama işlemi için bir uyarı mesajı
copied_label = tk.Label(root, text="", fg="green")
copied_label.pack(pady=5)

# Resimlerin yollarını gösterecek bir Frame ekleyelim
image_frame_label = tk.Label(root, text="Çıkarılan Resimler:")
image_frame_label.pack(pady=10)

image_frame = tk.Frame(root)
image_frame.pack(pady=10)

# Arayüzü başlatma
root.mainloop()
