import streamlit as st
import pandas as pd
import folium
import requests
import re
import io
import base64
from folium.features import DivIcon
from branca.element import Element

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="Генератор Карт Маршрутов", page_icon="🗺️", layout="wide")
OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
DEFAULT_CENTER = (46.4825, 30.7233)  # Одесса
MIN_POINTS_FOR_ROUTE = 2

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def image_to_base64(uploaded_file) -> str:
    """Кодує завантажений файл зображення в Base64."""
    if uploaded_file is None:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        encoded_string = base64.b64encode(bytes_data).decode('utf-8')
        mime_type = uploaded_file.type
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception:
        return None

def sanitize_filename(name: str) -> str:
    if not name:
        return "map_result"
    name = str(name).strip()
    name = re.sub(r'[\\/:"*?<>|]+', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 120:
        name = name[:120].rstrip()
    name = re.sub(r'[^\w\-. ]', '_', name)
    name = name.replace(' ', '_')
    return name or "map_result"

def detect_datetime_column(df: pd.DataFrame, exclude_indices: set):
    best_col = None
    best_count = 0
    best_parsed = None
    FORMATS_TO_TRY = ['%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M', '%Y/%m/%d %H:%M:%S', None]

    for col in df.columns:
        if not isinstance(col, int) or col in exclude_indices:
            continue
        parsed = None
        non_null = 0
        for fmt in FORMATS_TO_TRY:
            current_parsed = None
            try:
                if fmt is not None:
                    current_parsed = pd.to_datetime(df.iloc[:, col], format=fmt, errors='coerce')
                else:
                    current_parsed = pd.to_datetime(df.iloc[:, col], errors='coerce', dayfirst=False)
                current_non_null = current_parsed.notna().sum()
                if current_non_null > non_null:
                    non_null = current_non_null
                    parsed = current_parsed
                if fmt is not None and non_null > 0.9 * len(df) and len(df) > 0:
                    break
            except Exception:
                continue
        if non_null > best_count:
            best_count = non_null
            best_col = col
            best_parsed = parsed
    return best_col, best_parsed

def clean_coordinate(val):
    if pd.isna(val) or val == "":
        return None
    s = str(val).replace(',', '.').strip()
    s = s.replace(' ', '')
    try:
        return float(s)
    except ValueError:
        return None

# --- ОСНОВНАЯ ЛОГИКА ГЕНЕРАЦИИ ---

def generate_map_html(df: pd.DataFrame, logo_base64: str = None):
    # Проверки структуры
    if df.shape[1] <= 3:
        st.error("Недостаточно колонок: требуются C (index 2) => longitude и D (index 3) => latitude.")
        return None

    df = df.copy()
    # Координаты (индексы 2 и 3)
    df['longitude'] = df.iloc[:, 2].apply(clean_coordinate)
    df['latitude'] = df.iloc[:, 3].apply(clean_coordinate)
    df['is_valid_coord'] = df['longitude'].notna() & df['latitude'].notna()

    # Устройство (индекс 5)
    device_col = 5 if df.shape[1] > 5 else None

    # Datetime
    exclude = {2, 3}
    if device_col is not None:
        exclude.add(device_col)
    
    dt_col, dt_parsed = detect_datetime_column(df, exclude)
    if dt_col is not None and dt_parsed is not None:
        df['datetime'] = dt_parsed.reset_index(drop=True)
        df['date'] = df['datetime'].dt.date.where(df['datetime'].notna(), other=pd.NaT)
    else:
        df['date'] = 'all'
        df['datetime'] = pd.NaT

    df['date_str'] = df['date'].astype(str)
    df = df.sort_values(by=['date_str', 'datetime']).reset_index(drop=True)
    dates_list = sorted(df['date_str'].unique())

    # Центр карти
    valid_points = df[df['is_valid_coord']]
    if not valid_points.empty:
        center = [valid_points['latitude'].mean(), valid_points['longitude'].mean()]
    else:
        center = DEFAULT_CENTER

    m = folium.Map(location=center, zoom_start=12)
    layer_dict = {}
    
    # JSON для JS
    import json
    markers_for_js = []

    # 1. Создаем группы слоев и маршруты
    for idx_date, day_str in enumerate(dates_list):
        fg = folium.FeatureGroup(name=str(day_str), show=(idx_date == 0))
        m.add_child(fg)
        layer_dict[day_str] = fg

        group_valid = df[(df['date_str'] == day_str) & (df['is_valid_coord'])]
        points = list(zip(group_valid['longitude'], group_valid['latitude']))

        if len(points) >= MIN_POINTS_FOR_ROUTE:
            # Намагаємося побудувати маршрут через OSRM
            try:
                limit_osrm = 80
                step = max(1, len(points) // limit_osrm)
                route_input_points = points[::step]
                if points[-1] != route_input_points[-1]:
                    route_input_points.append(points[-1])
                
                coords_str = ";".join([f"{lon},{lat}" for lon, lat in route_input_points])
                url = OSRM_URL.format(coords=coords_str)
                
                resp = requests.get(url, timeout=10) # Таймаут
                if resp.status_code == 200:
                    data = resp.json()
                    if "routes" in data and data["routes"]:
                        geo = data["routes"][0]["geometry"]["coordinates"]
                        folium.PolyLine([(lat, lon) for lon, lat in geo], color="blue", weight=4, opacity=0.8).add_to(fg)
                        # Старт/Финиш
                        folium.Marker([(geo[0][1], geo[0][0])], tooltip="Start", icon=folium.Icon(color="green")).add_to(fg)
                        folium.Marker([(geo[-1][1], geo[-1][0])], tooltip="End", icon=folium.Icon(color="red")).add_to(fg)
                    else:
                        raise Exception("No routes found")
                else:
                    raise Exception("OSRM Error")
            except Exception:
                # Fallback: прямые линии
                folium.PolyLine([(lat, lon) for lon, lat in points], color="orange", weight=3, opacity=0.7, dash_array='5').add_to(fg)
                if points:
                    folium.Marker([points[0][1], points[0][0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(fg)
                    folium.Marker([points[-1][1], points[-1][0]], tooltip="End", icon=folium.Icon(color="red")).add_to(fg)
        elif len(points) == 1:
            folium.Marker([points[0][1], points[0][0]], tooltip="Single Point", icon=folium.Icon(color="blue")).add_to(fg)

    folium.LayerControl(collapsed=False).add_to(m)

    # 2. Таблица и маркеры
    table_rows_html = ""
    global_num = 1
    current_date_header = None

    for _, row in df.iterrows():
        num = global_num
        day_str = row['date_str']

        if day_str != current_date_header:
            current_date_header = day_str
            table_rows_html += f"""
            <tr style="background-color: #f3f4f6; color: #374151; font-weight: bold; border-top: 2px solid #e5e7eb;">
                <td colspan="3" style="text-align: center; padding: 6px;">{day_str}</td>
            </tr>
            """

        if pd.notna(row.get('datetime')):
            date_display = str(row.get('datetime'))
        else:
            date_display = str(day_str)

        device_val = ""
        if device_col is not None:
            val = row.get(device_col, "")
            device_val = "" if pd.isna(val) else str(val)

        if row['is_valid_coord']:
            lat, lon = row['latitude'], row['longitude']
            if day_str in layer_dict:
                icon_html = f'''<div style="display:inline-block; background:#1978c8; color:white; font-weight:bold; 
                            border-radius:14px; padding:4px 8px; box-shadow:0 0 2px rgba(0,0,0,0.6);">{num}</div>'''
                
                folium.Marker(
                    location=[lat, lon],
                    tooltip=f"#{num}",
                    popup=folium.Popup(f"#{num}<br>{date_display}<br>{device_val}", max_width=300),
                    icon=DivIcon(icon_size=(30, 30), icon_anchor=(15, 15), html=icon_html)
                ).add_to(layer_dict[day_str])
                
                markers_for_js.append({'num': num, 'day': str(day_str), 'lat': float(lat), 'lon': float(lon)})

            table_rows_html += f'<tr class="valid-row" data-day="{day_str}" data-num="{num}">' \
                               f'<td style="width:54px">{num}</td><td>{date_display}</td><td>{device_val}</td></tr>\n'
        else:
            raw_lon = str(row.iloc[2])[:10]
            raw_lat = str(row.iloc[3])[:10]
            table_rows_html += f'<tr style="color: #d32f2f; background-color: #fef2f2;">' \
                               f'<td style="width:54px">{num}</td>' \
                               f'<td>{date_display}<br><small style="opacity:0.7">Err: {raw_lat}, {raw_lon}</small></td>' \
                               f'<td>{device_val}</td></tr>\n'
        global_num += 1

    # Логотип
    logo_html = ""
    if logo_base64:
        logo_html = f"""
        <div style="position: absolute; top: 10px; right: 10px; z-index: 9999; 
                    background: rgba(255, 255, 255, 0.8); padding: 5px; border-radius: 5px;">
            <img src="{logo_base64}" style="width: auto; height: 40px; display: block;" alt="Logo">
        </div>
        """

    # CSS/JS Overlay
    overlay_html = f"""
    <style>
      #data-overlay {{
        position: absolute; right: 18px; bottom: 18px; width: 460px; max-height: 48vh;
        overflow: auto; background: rgba(255,255,255,0.96); border-radius: 10px;
        box-shadow: 0 6px 24px rgba(16,24,40,0.12); border: 1px solid rgba(0,0,0,0.05);
        font-family: Arial, sans-serif; z-index: 9999;
      }}
      #data-overlay header {{ padding:10px 12px; border-bottom:1px solid rgba(0,0,0,0.04); display:flex; justify-content:space-between; align-items:center; }}
      #data-overlay h4 {{ margin:0; font-size:14px; color:#0f1724; }}
      #data-overlay table {{ width:100%; border-collapse:collapse; font-size:13px; }}
      #data-overlay th, #data-overlay td {{ padding:8px 10px; text-align:left; border-bottom:1px solid rgba(15,23,36,0.04); }}
      tr.highlight td {{ background: linear-gradient(90deg, rgba(232,74,74,0.06), transparent); }}
      tr.valid-row:hover td {{ background: linear-gradient(90deg, rgba(43,139,230,0.03), transparent); cursor:pointer; }}
    </style>

    <div id="data-overlay">
      <header>
        <h4>Данные маршрута</h4>
        <button style="background:transparent;border:none;font-weight:700;cursor:pointer;color:#6b7280" onclick="document.getElementById('data-overlay').style.display='none'">✕</button>
      </header>
      <div style="padding:0 12px 12px 12px;">
        <table>
          <thead><tr><th>№</th><th>Дата</th><th>Устройство</th></tr></thead>
          <tbody>{table_rows_html}</tbody>
        </table>
      </div>
    </div>

    <script>
      window._maim_markers = {json.dumps(markers_for_js)};
      
      function getMapInstance() {{
          if(window.map) return window.map;
          // Пошук об'єкта карти Folium в глобальній області
          for(var key in window) {{
             if(window.hasOwnProperty(key) && window[key] && 
                typeof window[key].flyTo === 'function' && 
                typeof window[key]._layers === 'object') {{
                 window.map = window[key]; return window.map;
             }}
          }}
          return null;
      }}

      function centerOn(num, day) {{
        var map = getMapInstance();
        if(!map) return;
        var rec = window._maim_markers.find(r => r.num === num && r.day === String(day));
        if(rec) {{
          map.setView([rec.lat, rec.lon], 18, {{animate: true, duration: 0.5}});
          // Підсвічування рядка таблиці
          var rows = document.querySelectorAll('#data-overlay tr');
          rows.forEach(r => r.classList.remove('highlight'));
          var row = document.querySelector('#data-overlay tr[data-num="'+num+'"][data-day="'+day+'"]');
          if(row) {{
              row.classList.add('highlight');
              row.scrollIntoView({{behavior: "smooth", block: "center"}});
          }}
          // Открытие попапа
          map.eachLayer(function(layer) {{
              if (layer instanceof L.Marker) {{
                  var ll = layer.getLatLng();
                  if (Math.abs(ll.lat - rec.lat) < 0.000001 && Math.abs(ll.lng - rec.lon) < 0.000001) {{
                      layer.openPopup();
                  }}
              }}
          }});
        }}
      }}

      document.addEventListener('DOMContentLoaded', function() {{
        // Клик по таблице
        document.body.addEventListener('click', function(e){{
            var target = e.target.closest('tr.valid-row');
            if(target){{
                centerOn(parseInt(target.dataset.num), target.dataset.day);
            }}
        }});
        
        // Клик по маркерам (привязка)
        setTimeout(function(){{
            var map = getMapInstance();
            if(map && window._maim_markers){{
                map.eachLayer(function(layer) {{
                     if (layer instanceof L.Marker) {{
                          var ll = layer.getLatLng();
                          var d = window._maim_markers.find(m => Math.abs(m.lat - ll.lat) < 0.0001 && Math.abs(m.lon - ll.lng) < 0.0001);
                          if(d) {{
                              layer.on('click', function() {{ centerOn(d.num, d.day); }});
                          }}
                     }}
                }});
            }}
        }}, 2000);
      }});
    </script>
    """ + logo_html

    el = Element(overlay_html)
    m.get_root().html.add_child(el)
    
    # Возвращаем HTML как строку
    return m.get_root().render()

# --- ИНТЕРФЕЙС ---

def main():
    st.title("🗺️ Excel в Карту Маршрута")
    st.markdown("Завантажте Excel-файл, щоб побудувати карту переміщень з таблицею подій.")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Перетягніть Excel файл (.xlsx)", type=['xls', 'xlsx', 'xlsm'])
    
    with col2:
        uploaded_logo = st.file_uploader("Логотип (необов'язково)", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("🚀 Построить карту", type="primary"):
            with st.spinner('Читання файлу і побудова маршрутів...'):
                try:
                    # Определяем движок
                    ext = uploaded_file.name.split('.')[-1].lower()
                    engine = 'openpyxl' if ext in ['xlsx', 'xlsm', 'xltx'] else 'xlrd'
                    
                    # Читаємо ім'я файлу з B8 (для імені вихідного файлу)
                    out_name = "route_map.html"
                    try:
                        df_name = pd.read_excel(uploaded_file, engine=engine, usecols="B", header=None, skiprows=7, nrows=1)
                        val = str(df_name.iloc[0, 0])
                        if val and val != 'nan':
                            out_name = sanitize_filename(val) + ".html"
                    except:
                        pass

                    # Перемотуємо файл на початок і читаємо дані
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_excel(uploaded_file, engine=engine, header=None, skiprows=7)
                    except Exception:
                        # Fallback без движка
                        uploaded_file.seek(0)
                        df = pd.read_excel(uploaded_file, header=None, skiprows=7)

                    # Логотип
                    logo_b64 = image_to_base64(uploaded_logo) if uploaded_logo else None

                    # Генерация
                    html_content = generate_map_html(df, logo_b64)

                    if html_content:
                        st.success("Карта успешно создана!")
                        
                        # Кнопка скачивания
                        st.download_button(
                            label="💾 Завантажити карту (HTML)",
                            data=html_content,
                            file_name=out_name,
                            mime="text/html"
                        )
                        
                        # Попередній перегляд (iframe)
                        st.subheader("Попередній перегляд")
                        st.components.v1.html(html_content, height=600, scrolling=True)

                except Exception as e:
                    st.error(f"Помилка при обробці: {e}")
                    st.exception(e)

if __name__ == "__main__":
    main()
