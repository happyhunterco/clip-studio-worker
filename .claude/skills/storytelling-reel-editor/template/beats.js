// beats.js: what appears on screen, and when. Every time comes from the words being spoken:
//   W('phrase')        start of the first time this phrase is said     W('phrase', 20) = first time at/after 20 s
//   WE('phrase')       end of that phrase                              END = end of the video
// Only add what the creator asked for. Keep everything above their head and inside the safe area
// (y 192-1536; below y 960 stay left of x 900). Check with stills + safezone.mjs. See reference/components.md.
//
// Examples (delete or adapt):
//
// BEAT.notify({ app: 'tiktok', title: 'TikTok', body: 'Your video is in 300 view jail...', at: W('getting views'), until: W('this clip') - 0.04 });
// BEAT.notify({ app: 'stripe', title: 'Stripe', body: 'Someone asked for a refund', at: W('making money'), until: W('this clip') - 0.04 });
// BEAT.pill({ text: 'Sleep', at: W('while I sleep'), until: W('this clip') - 0.04 });
// BEAT.bubble({ app: 'claude', text: 'these will probably flop lol', sig: '-clanker 5.5', at: W('Claude agents'), until: W('last night') - 0.04, top: 560 });
// BEAT.grid({ app: 'claude', title: '6 ads', sub: 'edited last night', items: [1,2,3,4,5,6].map((n) => ({ src: `assets/ad${n}.jpg` })),
//             at: W('six ads'), until: W('getting views') - 0.04 });
// BEAT.comment({ account: 'yourhandle', word: 'Claude', at: W('comment'), typeEnd: WE('comment Claude') + 0.3 });
