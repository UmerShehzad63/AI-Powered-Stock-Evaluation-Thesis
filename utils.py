def normalize(value, min_val, max_val):
    if value < min_val: return 0
    if value > max_val: return 100
    return ((value - min_val) / (max_val - min_val)) * 100

def get_rating(score):
    if score >= 70: return "Strong Buy", "green"
    if score >= 60: return "Buy", "lightgreen"
    if score >= 40: return "Hold", "orange"
    if score >= 30: return "Sell", "red"
    return "Strong Sell", "darkred"