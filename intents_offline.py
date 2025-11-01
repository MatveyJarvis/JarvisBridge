# ===== Offline Intents (время, погода, калькулятор) =====
import datetime, math

def handle_offline_intent(text):
    t = text.lower()
    if 'время' in t:
        now = datetime.datetime.now().strftime('%H:%M')
        return f'Сейчас {now}'
    if 'дата' in t:
        return f'Сегодня {datetime.datetime.now().strftime("%d %B %Y")}'
    if any(x in t for x in ['плюс','минус','умнож','дел']):
        try:
            expr = (t.replace('плюс','+')
                      .replace('минус','-')
                      .replace('умножить','*')
                      .replace('разделить','/')
                      .replace('на','')
                      .replace(',','.'))
            res = eval(expr)
            return f'Результат {res}'
        except Exception:
            return 'Не удалось посчитать'
    if 'погода' in t:
        return 'Погода отличная, без осадков'
    return None

