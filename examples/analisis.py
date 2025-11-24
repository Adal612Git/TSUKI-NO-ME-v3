import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from collections import Counter
import string
import os

# Configuración de matplotlib para evitar errores
plt.rcParams['font.family'] = 'DejaVu Sans'

def limpiar_valores_numericos(valor):
    """Convierte valores como '15M+ (saga completa)' a numéricos"""
    if pd.isna(valor) or valor == '':
        return np.nan
    
    # Si ya es numérico, retornar como está
    if isinstance(valor, (int, float)):
        return float(valor)
    
    # Convertir string a numérico
    valor_str = str(valor).strip()
    
    # Manejar diferentes formatos
    if 'M' in valor_str or 'millones' in valor_str.lower():
        # Extraer número antes de M (millones)
        match = re.search(r'(\d+\.?\d*)\s*[M+]', valor_str)
        if match:
            return float(match.group(1)) * 1000000
        # Buscar solo números
        match = re.search(r'(\d+\.?\d*)', valor_str)
        if match:
            return float(match.group(1)) * 1000000
    
    elif 'K' in valor_str or 'mil' in valor_str.lower():
        # Extraer número antes de K (miles)
        match = re.search(r'(\d+\.?\d*)\s*[K]', valor_str)
        if match:
            return float(match.group(1)) * 1000
    
    # Intentar convertir directamente
    try:
        return float(valor_str)
    except:
        return np.nan

def procesar_columnas_numericas(df):
    """Limpia y convierte columnas numéricas del dataset"""
    # Columnas que deben ser numéricas
    columnas_numericas = {
        'Ventas estimadas': limpiar_valores_numericos,
        'Rating promedio (1-5)': lambda x: float(x) if pd.notna(x) and str(x).replace('.', '').isdigit() else np.nan,
        'numero_resenas': lambda x: int(x) if pd.notna(x) and str(x).replace('.', '').isdigit() else np.nan,
        'semanas_lista_bestseller': lambda x: int(x) if pd.notna(x) and str(x).isdigit() else np.nan,
        'traduccion_idiomas': lambda x: int(x) if pd.notna(x) and str(x).isdigit() else np.nan
    }
    
    df_limpio = df.copy()
    
    for col, funcion in columnas_numericas.items():
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].apply(funcion)
            print(f"  ✅ Columna {col} convertida a numérica")
    
    return df_limpio

class AnalizadorTextosSimple:
    def __init__(self):
        # Listas de palabras emocionales en español e inglés
        self.palabras_positivas = [
            'amor', 'feliz', 'alegría', 'éxito', 'bueno', 'hermoso', 'maravilloso',
            'fantástico', 'increíble', 'perfecto', 'ganar', 'victoria', 'sonrisa', 'risa',
            'bello', 'dichoso', 'contento', 'gozo', 'placer', 'suerte', 'fortuna',
            'triunfo', 'logro', 'conquista', 'celebración', 'fiesta', 'abrazar', 'besar',
            'pasión', 'deseo', 'esperanza', 'fe', 'confianza', 'optimismo', 'brillante',
            'radiante', 'espléndido', 'magnífico', 'extraordinario', 'asombroso'
        ]
        
        self.palabras_negativas = [
            'miedo', 'triste', 'dolor', 'muerte', 'malo', 'horrible', 'terrible',
            'pérdida', 'fracaso', 'odio', 'enojo', 'ira', 'desastre', 'catástrofe',
            'tragedia', 'sufrimiento', 'agonía', 'tortura', 'miseria', 'pobreza',
            'enfermedad', 'virus', 'pandemia', 'guerra', 'conflicto', 'violencia',
            'sangre', 'asesinato', 'crimen', 'peligro', 'amenaza', 'miedo', 'terror',
            'pánico', 'desesperación', 'soledad', 'abandono', 'traición', 'engaño',
            'mentira', 'corrupción'
        ]
        
        # Stopwords básicas en español e inglés
        self.stop_words = {
            'español': {
                'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para',
                'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o',
                'este', 'sí', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también',
                'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'estados',
                'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e',
                'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él',
                'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella',
                'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu',
                'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías',
                'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro',
                'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras',
                'esos', 'esas', 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'esté',
                'estés', 'estemos', 'estéis', 'estén', 'estaré', 'estarás', 'estará', 'estaremos',
                'estaréis', 'estarán', 'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían',
                'estaba', 'estabas', 'estábamos', 'estabais', 'estaban', 'estuve', 'estuviste',
                'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron', 'estuviera', 'estuvieras',
                'estuviéramos', 'estuvierais', 'estuvieran', 'estuviese', 'estuvieses',
                'estuviésemos', 'estuvieseis', 'estuviesen', 'estando', 'estado', 'estada',
                'estados', 'estadas', 'estad', 'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haya',
                'hayas', 'hayamos', 'hayáis', 'hayan', 'habré', 'habrás', 'habrá', 'habremos',
                'habréis', 'habrán', 'habría', 'habrías', 'habríamos', 'habríais', 'habrían',
                'había', 'habías', 'habíamos', 'habíais', 'habían', 'hube', 'hubiste', 'hubo',
                'hubimos', 'hubisteis', 'hubieron', 'hubiera', 'hubieras', 'hubiéramos',
                'hubierais', 'hubieran', 'hubiese', 'hubieses', 'hubiésemos', 'hubieseis',
                'hubiesen', 'habiendo', 'habido', 'habida', 'habidos', 'habidas', 'soy', 'eres',
                'es', 'somos', 'sois', 'son', 'sea', 'seas', 'seamos', 'seáis', 'sean', 'seré',
                'serás', 'será', 'seremos', 'seréis', 'serán', 'sería', 'serías', 'seríamos',
                'seríais', 'serían', 'era', 'eras', 'éramos', 'erais', 'eran', 'fui', 'fuiste',
                'fue', 'fuimos', 'fuisteis', 'fueron', 'fuera', 'fueras', 'fuéramos', 'fuerais',
                'fueran', 'fuese', 'fueses', 'fuésemos', 'fueseis', 'fuesen', 'sintiendo',
                'sentido', 'tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen', 'tenga',
                'tengas', 'tengamos', 'tengáis', 'tengan', 'tendré', 'tendrás', 'tendrá',
                'tendremos', 'tendréis', 'tendrán', 'tendría', 'tendrías', 'tendríamos',
                'tendríais', 'tendrían', 'tenía', 'tenías', 'teníamos', 'teníais', 'tenían',
                'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron', 'tuviera',
                'tuvieras', 'tuviéramos', 'tuvierais', 'tuvieran', 'tuviese', 'tuvieses',
                'tuviésemos', 'tuvieseis', 'tuviesen', 'teniendo', 'tenido', 'tenida', 'tenidos',
                'tenidas', 'tened'
            },
            'inglés': {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
                "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
                'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
                'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
                'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
                'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
                'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
                'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
                'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
                'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
                'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
                'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now',
                'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
                'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven',
                "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn',
                "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren',
                "weren't", 'won', "won't", 'wouldn', "wouldn't"
            }
        }

    def limpiar_texto(self, texto):
        """Limpia el texto eliminando caracteres no deseados"""
        if not texto:
            return ""
        # Eliminar caracteres especiales pero mantener puntuación básica
        texto = re.sub(r'[^\w\s.,!?;:()\-]', '', texto)
        return texto.strip()
    
    def detectar_idioma(self, texto):
        """Detecta el idioma basado en palabras comunes"""
        palabras = texto.lower().split()[:200]  # Primeras 200 palabras
        es_count = len([p for p in palabras if p in self.stop_words['español']])
        en_count = len([p for p in palabras if p in self.stop_words['inglés']])
        
        if es_count > en_count and es_count > 5:
            return "español"
        elif en_count > es_count and en_count > 5:
            return "inglés"
        else:
            return "indeterminado"
    
    def calcular_legibilidad_simple(self, texto):
        """Calcula una métrica simple de legibilidad"""
        # Métrica basada en longitud promedio de oraciones y palabras
        oraciones = re.split(r'[.!?]+', texto)
        oraciones = [o.strip() for o in oraciones if o.strip()]
        
        if not oraciones:
            return 50  # Valor por defecto
        
        palabras_por_oracion = []
        letras_por_palabra = []
        
        for oracion in oraciones[:50]:  # Muestra de 50 oraciones
            palabras = oracion.split()
            if palabras:
                palabras_por_oracion.append(len(palabras))
                for palabra in palabras:
                    letras_por_palabra.append(len(palabra))
        
        if not palabras_por_oracion:
            return 50
        
        avg_palabras_oracion = np.mean(palabras_por_oracion)
        avg_letras_palabra = np.mean(letras_por_palabra) if letras_por_palabra else 5
        
        # Fórmula simplificada de legibilidad
        legibilidad = 100 - (avg_palabras_oracion * 1.5 + avg_letras_palabra * 10)
        return max(0, min(100, legibilidad))
    
    def analizar_sentimiento_basico(self, texto):
        """Análisis básico de sentimiento"""
        texto_lower = texto.lower()
        palabras = texto_lower.split()
        
        pos_count = sum(1 for palabra in palabras if palabra in self.palabras_positivas)
        neg_count = sum(1 for palabra in palabras if palabra in self.palabras_negativas)
        total_palabras_emocionales = pos_count + neg_count
        
        if total_palabras_emocionales > 0:
            ratio_positivo = pos_count / total_palabras_emocionales
            ratio_negativo = neg_count / total_palabras_emocionales
            compuesto = (pos_count - neg_count) / max(1, total_palabras_emocionales)
        else:
            ratio_positivo = ratio_negativo = compuesto = 0.5
        
        return {
            'positivo': ratio_positivo,
            'negativo': ratio_negativo,
            'neutral': 1.0 - (ratio_positivo + ratio_negativo),
            'compuesto': compuesto,
            'total_emocional': total_palabras_emocionales
        }
    
    def analizar_libro(self, file_path):
        """Analiza un libro y extrae métricas textuales"""
        try:
            # Intentar diferentes codificaciones
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            texto = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                        texto = file.read()
                    if len(texto) > 1000:  # Texto suficientemente largo
                        break
                except:
                    continue
            
            if texto is None or len(texto) < 1000:
                return None
                
        except Exception as e:
            print(f"    Error leyendo archivo {file_path}: {e}")
            return None
        
        texto = self.limpiar_texto(texto)
        if len(texto) < 1000:
            return None
        
        # Métricas básicas
        palabras = texto.split()
        oraciones = re.split(r'[.!?]+', texto)
        oraciones = [o.strip() for o in oraciones if o.strip()]
        
        # Filtrar stopwords
        idioma = self.detectar_idioma(texto)
        stop_words_usar = self.stop_words.get(idioma, set())
        palabras_sin_stop = [p for p in palabras if p.lower() not in stop_words_usar and p not in string.punctuation]
        
        # Análisis de sentimiento
        sentimiento = self.analizar_sentimiento_basico(texto)
        
        # Métricas de estructura
        longitud_promedio_oraciones = np.mean([len(o.split()) for o in oraciones[:100]]) if oraciones else 0
        longitud_promedio_palabras = np.mean([len(p) for p in palabras_sin_stop[:1000]]) if palabras_sin_stop else 0
        
        # Densidad de diálogo (aproximado)
        dialogos = len(re.findall(r'["«»"''].*?["«»"'']', texto))
        densidad_dialogo = dialogos / len(oraciones) if oraciones else 0
        
        # Vocabulario único
        vocabulario_unico = len(set(palabras_sin_stop[:5000]))
        ratio_vocabulario = vocabulario_unico / len(palabras_sin_stop[:5000]) if palabras_sin_stop else 0
        
        # Legibilidad simple
        legibilidad = self.calcular_legibilidad_simple(texto)
        
        return {
            'longitud_texto': len(texto),
            'num_palabras': len(palabras),
            'num_oraciones': len(oraciones),
            'longitud_promedio_oracion': longitud_promedio_oraciones,
            'longitud_promedio_palabra': longitud_promedio_palabras,
            'densidad_dialogo': densidad_dialogo,
            'vocabulario_unico': vocabulario_unico,
            'ratio_vocabulario': ratio_vocabulario,
            'legibilidad_simple': legibilidad,
            'sentimiento_positivo': sentimiento['positivo'],
            'sentimiento_negativo': sentimiento['negativo'],
            'sentimiento_neutral': sentimiento['neutral'],
            'sentimiento_compuesto': sentimiento['compuesto'],
            'palabras_emocionales_positivas': sum(1 for p in palabras if p in self.palabras_positivas),
            'palabras_emocionales_negativas': sum(1 for p in palabras if p in self.palabras_negativas),
            'idioma': idioma,
            'tasa_palabras_emocionales': sentimiento['total_emocional'] / len(palabras) if palabras else 0
        }

def procesar_dataset_libros():
    """Procesa el dataset existente y añade métricas textuales"""
    
    # Cargar dataset existente
    try:
        df_existente = pd.read_csv('LibrosDataset - Libros.csv')
        print(f"✅ Dataset cargado: {len(df_existente)} libros")
        print(f"Columnas disponibles: {list(df_existente.columns)}")
        
        # Usar las columnas que ya tienes en tu dataset
        df_combinado = df_existente.copy()
        
        # Crear columnas de título y autor usando las que ya existen
        if 'probable_title' in df_combinado.columns:
            df_combinado['titulo_final'] = df_combinado['probable_title']
        else:
            df_combinado['titulo_final'] = df_combinado['filename']
            
        if 'probable_author' in df_combinado.columns:
            df_combinado['autor_final'] = df_combinado['probable_author']
        else:
            df_combinado['autor_final'] = 'Desconocido'
            
    except Exception as e:
        print(f"❌ No se pudo cargar el dataset existente: {e}")
        # Crear dataset básico desde los archivos
        directorio_libros = Path('C:/Users/romer/OneDrive/Desktop/Libros')
        archivos = list(directorio_libros.glob('*.*'))
        df_combinado = pd.DataFrame({
            'filename': [f.name for f in archivos],
            'titulo_final': [f.stem for f in archivos],
            'autor_final': 'Desconocido'
        })
        print(f"✅ Dataset básico creado: {len(df_combinado)} archivos")
    
    # Inicializar analizador
    analizador = AnalizadorTextosSimple()
    
    # Lista para almacenar resultados
    metricas_texto = []
    
    # Procesar cada libro
    directorio_libros = Path('C:/Users/romer/OneDrive/Desktop/Libros')
    
    for idx, libro in df_combinado.iterrows():
        filename = libro['filename']
        file_path = directorio_libros / filename
        
        print(f"📖 Analizando ({idx+1}/{len(df_combinado)}): {filename}")
        
        if file_path.exists() and file_path.is_file():
            metricas = analizador.analizar_libro(str(file_path))
            if metricas:
                metricas['filename'] = filename
                metricas_texto.append(metricas)
                print(f"  ✅ Analizado: {len(metricas_texto)} libros procesados")
            else:
                print(f"  ⚠️ No se pudo analizar (texto muy corto o error)")
        else:
            print(f"  ❌ Archivo no encontrado: {filename}")
    
    # Crear DataFrame con métricas
    if metricas_texto:
        df_metricas = pd.DataFrame(metricas_texto)
        
        # Combinar con dataset original
        df_final = df_combinado.merge(df_metricas, on='filename', how='left')
        
        # Guardar dataset enriquecido
        df_final.to_csv('dataset_libros_enriquecido.csv', index=False)
        print(f"✅ Dataset enriquecido guardado: {len(df_final)} libros")
        print(f"📊 Métricas extraídas para: {len(df_metricas)} libros")
        
        return df_final
    else:
        print("❌ No se pudieron extraer métricas de ningún libro")
        return None

def mostrar_resumen_estadisticas(df):
    """Muestra un resumen de las estadísticas"""
    print("\n" + "="*60)
    print("📊 RESUMEN ESTADÍSTICO DE MÉTRICAS TEXTUALES")
    print("="*60)
    
    metricas_numericas = ['num_palabras', 'legibilidad_simple', 'sentimiento_compuesto', 
                         'longitud_promedio_oracion', 'ratio_vocabulario']
    
    for metrica in metricas_numericas:
        if metrica in df.columns:
            datos = df[metrica].dropna()
            if len(datos) > 0:
                print(f"\n{metrica.upper().replace('_', ' ')}:")
                print(f"  Mínimo: {datos.min():.2f}")
                print(f"  Máximo: {datos.max():.2f}")
                print(f"  Promedio: {datos.mean():.2f}")
                print(f"  Mediana: {datos.median():.2f}")
                print(f"  Libros con datos: {len(datos)}")
    
    if 'idioma' in df.columns:
        print(f"\nDISTRIBUCIÓN POR IDIOMA:")
        print(df['idioma'].value_counts())

def analizar_correlaciones_exito(df):
    """Analiza correlaciones entre métricas textuales y éxito"""
    # Primero limpiar las columnas numéricas
    df_limpio = procesar_columnas_numericas(df)
    
    # Métricas de éxito que podrías tener
    metricas_exito = ['Ventas estimadas', 'Rating promedio (1-5)', 'numero_resenas']
    
    # Métricas textuales
    metricas_texto = ['num_palabras', 'legibilidad_simple', 'sentimiento_compuesto', 
                     'longitud_promedio_oracion', 'ratio_vocabulario', 'densidad_dialogo']
    
    # Verificar qué métricas de éxito están disponibles y tienen datos
    metricas_exito_disponibles = []
    for m in metricas_exito:
        if m in df_limpio.columns and df_limpio[m].notna().sum() > 5:  # Al menos 5 datos
            metricas_exito_disponibles.append(m)
    
    metricas_texto_disponibles = [m for m in metricas_texto if m in df_limpio.columns]
    
    if metricas_exito_disponibles and metricas_texto_disponibles:
        print("\n" + "="*60)
        print("🔍 CORRELACIONES ENTRE MÉTRICAS TEXTUALES Y ÉXITO")
        print("="*60)
        
        # Crear visualización de correlaciones
        fig, axes = plt.subplots(1, len(metricas_exito_disponibles), figsize=(15, 5))
        if len(metricas_exito_disponibles) == 1:
            axes = [axes]
        
        for i, exito in enumerate(metricas_exito_disponibles):
            print(f"\n📈 {exito}:")
            correlaciones = []
            
            for texto in metricas_texto_disponibles:
                # Filtrar filas donde ambos valores no sean NaN
                datos_validos = df_limpio[[exito, texto]].dropna()
                if len(datos_validos) > 5:
                    correlacion = datos_validos[exito].corr(datos_validos[texto])
                    correlaciones.append((texto, correlacion))
                    print(f"  {texto}: {correlacion:.3f}")
            
            # Crear gráfico de barras para las correlaciones
            if correlaciones:
                textos, corrs = zip(*correlaciones)
                axes[i].bar(textos, corrs, color=['skyblue' if x > 0 else 'lightcoral' for x in corrs])
                axes[i].set_title(f'Correlaciones con {exito}')
                axes[i].set_ylabel('Correlación')
                axes[i].tick_params(axis='x', rotation=45)
                axes[i].axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('correlaciones_exito.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Gráfico de correlaciones guardado como 'correlaciones_exito.png'")
        
    else:
        print("⚠️ No hay suficientes datos de éxito para analizar correlaciones")

def crear_visualizaciones_avanzadas(df):
    """Crea visualizaciones más avanzadas de las métricas"""
    try:
        # Configuración de estilo
        plt.style.use('default')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # 1. Distribución de número de palabras
        if 'num_palabras' in df.columns:
            axes[0,0].hist(df['num_palabras'].dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0,0].set_title('Distribución de Número de Palabras')
            axes[0,0].set_xlabel('Número de Palabras')
            axes[0,0].set_ylabel('Frecuencia')
        
        # 2. Legibilidad vs Sentimiento
        if 'legibilidad_simple' in df.columns and 'sentimiento_compuesto' in df.columns:
            scatter = axes[0,1].scatter(df['legibilidad_simple'], df['sentimiento_compuesto'], 
                                       alpha=0.6, c=df.get('num_palabras', 100000), cmap='viridis')
            axes[0,1].set_title('Legibilidad vs Sentimiento')
            axes[0,1].set_xlabel('Legibilidad')
            axes[0,1].set_ylabel('Sentimiento Compuesto')
            if 'num_palabras' in df.columns:
                plt.colorbar(scatter, ax=axes[0,1], label='Número de Palabras')
        
        # 3. Densidad de diálogo por idioma
        if 'densidad_dialogo' in df.columns and 'idioma' in df.columns:
            df_boxplot = df[['idioma', 'densidad_dialogo']].dropna()
            if not df_boxplot.empty:
                sns.boxplot(data=df_boxplot, x='idioma', y='densidad_dialogo', ax=axes[0,2])
                axes[0,2].set_title('Densidad de Diálogo por Idioma')
                axes[0,2].set_xlabel('Idioma')
                axes[0,2].set_ylabel('Densidad de Diálogo')
        
        # 4. Ratio de vocabulario vs Longitud promedio de oración
        if 'ratio_vocabulario' in df.columns and 'longitud_promedio_oracion' in df.columns:
            axes[1,0].scatter(df['longitud_promedio_oracion'], df['ratio_vocabulario'], alpha=0.6, color='purple')
            axes[1,0].set_title('Complejidad Léxica vs Longitud de Oración')
            axes[1,0].set_xlabel('Longitud Promedio de Oración')
            axes[1,0].set_ylabel('Ratio de Vocabulario Único')
        
        # 5. Palabras emocionales positivas vs negativas
        if 'palabras_emocionales_positivas' in df.columns and 'palabras_emocionales_negativas' in df.columns:
            axes[1,1].scatter(df['palabras_emocionales_positivas'], df['palabras_emocionales_negativas'], 
                             alpha=0.6, color='orange')
            axes[1,1].set_title('Palabras Emocionales: Positivas vs Negativas')
            axes[1,1].set_xlabel('Palabras Positivas')
            axes[1,1].set_ylabel('Palabras Negativas')
        
        # 6. Distribución por género (si existe)
        if 'Genero' in df.columns:
            top_generos = df['Genero'].value_counts().head(10)
            axes[1,2].pie(top_generos.values, labels=top_generos.index, autopct='%1.1f%%')
            axes[1,2].set_title('Top 10 Géneros')
        
        plt.tight_layout()
        plt.savefig('metricas_textuales_avanzadas.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Visualizaciones avanzadas guardadas como 'metricas_textuales_avanzadas.png'")
        
    except Exception as e:
        print(f"⚠️ Error creando visualizaciones avanzadas: {e}")

def main():
    """Función principal"""
    print("📚 ANALIZADOR DE MÉTRICAS TEXTUALES - VERSIÓN COMPLETA")
    print("=" * 70)
    
    # Procesar libros y enriquecer dataset
    df_enriquecido = procesar_dataset_libros()
    
    if df_enriquecido is not None:
        print(f"\n✅ Dataset enriquecido con {len(df_enriquecido)} libros")
        print(f"📊 Métricas extraídas para: {df_enriquecido['num_palabras'].notna().sum()} libros")
        
        # Mostrar resumen estadístico
        mostrar_resumen_estadisticas(df_enriquecido)
        
        # Analizar correlaciones con éxito
        analizar_correlaciones_exito(df_enriquecido)
        
        # Crear visualizaciones avanzadas
        print("\n📈 CREANDO VISUALIZACIONES AVANZADAS...")
        crear_visualizaciones_avanzadas(df_enriquecido)
        
        print("\n🎯 ANÁLISIS COMPLETADO!")
        print("\n📁 ARCHIVOS GENERADOS:")
        print("  - dataset_libros_enriquecido.csv (dataset completo con métricas)")
        print("  - metricas_textuales_avanzadas.png (visualizaciones detalladas)")
        print("  - correlaciones_exito.png (análisis de correlaciones)")
        
        # Mostrar insights interesantes
        print("\n💡 INSIGHTS INTERESANTES:")
        
        if 'num_palabras' in df_enriquecido.columns:
            libro_mas_largo = df_enriquecido.loc[df_enriquecido['num_palabras'].idxmax()]
            libro_mas_corto = df_enriquecido.loc[df_enriquecido['num_palabras'].idxmin()]
            print(f"  📖 Libro más largo: {libro_mas_largo['titulo_final']} ({libro_mas_largo['num_palabras']:,} palabras)")
            print(f"  📖 Libro más corto: {libro_mas_corto['titulo_final']} ({libro_mas_corto['num_palabras']:,} palabras)")
        
        if 'sentimiento_compuesto' in df_enriquecido.columns:
            libro_mas_positivo = df_enriquecido.loc[df_enriquecido['sentimiento_compuesto'].idxmax()]
            libro_mas_negativo = df_enriquecido.loc[df_enriquecido['sentimiento_compuesto'].idxmin()]
            print(f"  😊 Libro más positivo: {libro_mas_positivo['titulo_final']} ({libro_mas_positivo['sentimiento_compuesto']:.2f})")
            print(f"  😔 Libro más negativo: {libro_mas_negativo['titulo_final']} ({libro_mas_negativo['sentimiento_compuesto']:.2f})")
        
        print(f"\n  🌐 Distribución por idioma:")
        if 'idioma' in df_enriquecido.columns:
            for idioma, count in df_enriquecido['idioma'].value_counts().items():
                print(f"     {idioma}: {count} libros")
        
    else:
        print("❌ No se pudo completar el análisis")

if __name__ == "__main__":
    main()