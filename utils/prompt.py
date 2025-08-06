
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from huggingface_hub import InferenceClient
import streamlit as st



def build_prompt(text, slide_count=6, include_visuals=False):
    remaining = slide_count - 3

    if include_visuals:
        main = remaining // 2
        extra = remaining % 2  # will be 1 if odd
        if extra == 1:
            main += 1
        else:
            slide_count = main + 3
        note = (
            "• Qeyd: Slayd sayı tam bölünmədiyi üçün sonuncu Əsas slayd `visual.type = 'none'` olaraq təyin edilməlidir."
            if extra == 1 else ""
        )
    else:
        main = remaining
        note = ""
    return f"""
Sənə bir sənədin mətni təqdim olunur. Bu mətni təhlil et və təqdimat üçün aşağıdakı struktura uyğun slayd formatında hazırla:

TƏQDİMATIN STRUKTURU:
1. Başlıq – Təqdimatın adı 
2. Giriş – Məqsəd və təqdim olunacaq mövzu üzrə qısa xülasə
3. Əsas Slaydlar – Mətndəki əsas mövzulardan hər biri üçün ayrıca slayd:
   • Hər biri unikal başlığa sahib olmalıdır  
   • Hər slaydda **4 əsas bənd** olmalıdır  
   • Slayd sayı: İstifadəçi {slide_count} slayd istəmişdir, bu saydan **1 başlıq**, **1 giriş**, **1 tövsiyə** slayd çıxıldıqdan sonra qalan **{main}** slayd əsas mövzular üçün istifadə olunmalıdır. 
4. Tövsiyə – Gələcək inkişaf və təkmilləşdirmə üçün 4–5 bəndlik təkliflər.

QAYDALAR:
- İstifadəçi {slide_count} slayd istəmişdir. Mətni analiz et və bu sayda slayda uyğun şəkildə ayır.
- Hər slayd üçün JSON obyektində aşağıdakı sahələri yaz:
  - type: "title" | "intro" | "main" | "recommendation"
  - Başlıq üçün (type = "title"):
    • title (təqdimatın adı)
  - Giriş üçün (type = "intro"):
    • aim (təqdimatın məqsədi)
    • summary (layihənin qısa xülasəsi, 3-4 cümlə)
  - Əsas slaydlar üçün (type = "main"):
    • title (slaydın başlığı)
    • point1, point2, point3, point4 (hər biri əsas məzmun bəndləri)
    • visual (vizual təklif üçün JSON obyekti, aşağıdakı formatda)
  - Tövsiyə slaydı üçün (type = "recommendation"):
    • recommendation1, recommendation2, recommendation3, recommendation4, (optional) recommendation5
- Hər slayd üçün:
  • Mətni slayd sayına uyğun şəkildə bərabər böl.
  • Cümlə dəyərlərinin içində qaçırılmamış qoşa dırnaq işarələrindən istifadə etmə. Daxili dırnaq işarələri üçün tək dırnaqdan istifadə et.
  • Lazımsız təkrarlardan, çox uzun cümlələrdən qaç.
  • Slayd dili **rəsmi və aydın olmalıdır**.
  • Əgər statistik və ya əsas nəticələr varsa, Əsas Göstəricilər slaydına daxil et.
  • Slaydların məzmunu yalnız sənədə əsaslanmalıdır, əlavə məlumat əlavə etmə.
  {note}

- Vizual təklif JSON formatı (mümkün olduqca fərqli növ vizuallar əlavə et, type image daxil olmaqla.):
    ```json
    {{
        "type": "none" | "image" | "bar" | "pie" | "line",
        "title": "Vizualın başlığı",
        "description": "Əgər type 'image'dirsə, burada şəkilin ətraflı təsviri verilir. Digər hallarda boş saxlanılır.",
        "xlabel": "X oxunun etiketi (əgər tətbiq olunursa)",
        "ylabel": "Y oxunun etiketi (əgər tətbiq olunursa)",
        "x": ["X oxundakı dəyərlər (əgər varsa)"],
        "y": ["Y oxundakı dəyərlər (əgər varsa)"],
        "labels": ["Dilim adları (əgər 'pie' tipi tətbiq olunursa)"],
        "sizes": ["Dilim ölçüləri (əgər 'pie' tipi tətbiq olunursa)"]
    }}
    ```

    - `type` sahəsi yalnız aşağıdakı dəyərlərdən biri ola bilər: "none", "image", "bar", "pie", "line"
    - `type` = "image" olduqda, `description` sahəsi vacibdir və şəkilin məzmununu izah etməlidir.
    - `type` = "bar" və ya "line" olduqda x, y, xlabel, ylabel sahələri dolu olmalıdır.
    -  Əgər uyğun vizual yoxdursa, `type` dəyəri `"none"` olmalıdır.
    - `type` = "pie" olduqda labels və sizes sahələri dolu olmalı, `x`, `y`, `xlabel`, `ylabel` isə boş buraxılmalıdır.
    - `type` = "none" olduqda digər sahələr boş buraxılmalıdır.

TƏHLİL EDİLƏCƏK SƏNƏDİN MƏTNI:
\"\"\"
{text}
\"\"\"

CAVABI BU FORMATA JSON ARRAY KİMİ QAYTAR:

```json
[
  {{
    "type": "title",
    "title": "Təqdimatın adı",
  }},
  {{
    "type": "intro",
    "aim": "Təqdimatın məqsədi",
    "summary": "Layihənin qısa xülasəsi"
  }},
  {{
    "type": "main",
    "title": "Əsas mövzunun başlığı",
    "point1": "...",
    "point2": "...",
    "point3": "...",
    "point4": "...",
    "visual": {{
      "type": "bar",
      "title": "",
      "description": "",
      "xlabel": "",
      "ylabel": "",
      "x": [],
      "y": [],
      "labels": [],
      "sizes": []
    }}
  }},
  ...
  {{
    "type": "recommendation",
    "recommendation1": "...",
    "recommendation2": "...",
    "recommendation3": "...",
    "recommendation4": "...",
    "recommendation5": "..."
  }}
]
```
"""


def get_presentation(text, slide_count=6, model_name='gemini-1.5-flash', include_visuals=False):
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    prompt = build_prompt(text, slide_count, include_visuals)
    print(prompt)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction="Sən təqdimat üzrə Azərbaycan dilində AI asistentsən."
    )

    generation_config = GenerationConfig(
        temperature=0.3,  # Controls randomness. Lower values are more deterministic.
    )

    try:
        # Send the prompt to the Gemini model
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            generation_config=generation_config
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            print("Error: Model did not return expected content structure.")
            return "Content generation failed."

    except Exception as e:
        print(f"An error occurred during content generation: {e}")
        return f"Error: {e}"


def generate_image_hf(prompt, output_path):
    client = InferenceClient(
        provider="hf-inference",
        api_key=st.secrets["HF_API_KEY"]

    )

    # This returns a PIL.Image object
    image = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-3-medium-diffusers",
    )

    # Save PIL image to file
    image.save(output_path)
    return output_path