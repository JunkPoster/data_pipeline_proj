-- This query shows how much each company has spent in auctions, how many events they've created, 
-- and an arbitrary calculation to represent their return-on-investment (extremely rudimentary and probably inaccurate).
SELECT
	co.company_id,
	co.company_name,
	SUM(au.bid_amount) AS total_bids,
	COUNT(ev.event_id) AS total_events,
	ROUND(NULLIF(COUNT(ev.event_id), 0) / SUM(au.bid_amount), 3) AS avg_dollar_per_event
FROM 
	companies co
LEFT JOIN auctions au
	ON co.company_id = au.company_id
LEFT JOIN raw_events ev
	ON co.company_id = ev.company_id
GROUP BY co.company_id
ORDER BY 
	total_bids DESC