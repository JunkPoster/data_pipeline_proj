SELECT
	ev.event_id,
	ev.event_type,
	us.user_name,
	us.user_email,
	co.company_name,
	ad.ad_type,
	ad.ad_category,
	au.bid_amount,
	dv.device_type
FROM events ev
LEFT JOIN users us
	ON ev.user_id = us.user_id
LEFT JOIN companies co
	ON ev.company_id = co.company_id
LEFT JOIN ads ad
	ON ev.ad_id = ad.ad_id
LEFT JOIN devices dv
	ON ev.device_id = dv.device_id
LEFT JOIN auctions au
	ON ev.auction_id = au.auction_id
ORDER BY us.user_name