def calculate_precision_recall(true_matches, predicted_matches):
    true_set = set(tuple(sorted(pair)) for pair in true_matches)
    predicted_set = set(tuple(sorted(pair)) for pair in predicted_matches)

    tp = len(true_set & predicted_set)
    fp = len(predicted_set - true_set)
    fn = len(true_set - predicted_set)

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    if precision + recall:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = 0

    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3)
    }