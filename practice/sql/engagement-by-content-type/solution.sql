SELECT content_type,
      SUM(CASE WHEN duration_seconds IS NULL THEN 0 ELSE duration_seconds END) AS total_duration,
      COUNT(content_type) AS item_count
FROM content_items
GROUP BY content_type
ORDER BY total_duration DESC
