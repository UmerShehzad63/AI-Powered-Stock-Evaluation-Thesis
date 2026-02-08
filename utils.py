def normalize(value, min_val, max_val):
    if value < min_val: return 0
    if value > max_val: return 100
    return ((value - min_val) / (max_val - min_val)) * 100

def get_rating(score):
    if score >= 80: return "Strong Bullish 🐂", "green"
    if score >= 60: return "Bullish Bias 📈", "#00CC96"
    if score >= 40: return "Neutral / Mixed 😐", "orange"
    if score >= 20: return "Bearish Bias 📉", "#FF4B4B"
    return "Strong Bearish 🐻", "darkred"