# Automated FFmpeg Clip Extraction Script for Kuku Microdramas
# Usage: bash cut_promos.sh (Linux/Mac) or run cut_promos.bat (Windows)
mkdir -p promo_clips

# Rank #1 (Ep 3 | 30.3s): Opens with NOBLE MATRIARCH declaring: 'You have hu
ffmpeg -y -ss 00:00:25.90 -to 00:00:56.20 -i "videos/episode_003.mp4" -c copy "promo_clips/promo_rank01_ep03_30s.mp4"

# Rank #2 (Ep 1 | 23.2s): Opens with LADY IN GOLD GOWN declaring: 'Long enou
ffmpeg -y -ss 00:01:15.00 -to 00:01:38.20 -i "videos/episode_001.mp4" -c copy "promo_clips/promo_rank02_ep01_23s.mp4"

# Rank #3 (Ep 1 | 31.8s): Opens with MATRIARCH declaring: 'You should turn a
ffmpeg -y -ss 00:00:11.30 -to 00:00:43.10 -i "videos/episode_001.mp4" -c copy "promo_clips/promo_rank03_ep01_31s.mp4"

# Rank #4 (Ep 2 | 32.4s): Opens with THE FORMER GROOM declaring: 'I cannot m
ffmpeg -y -ss 00:00:00.00 -to 00:00:32.40 -i "videos/episode_002.mp4" -c copy "promo_clips/promo_rank04_ep02_32s.mp4"

# Rank #5 (Ep 3 | 30.9s): Opens with THE BEARDED STRANGER declaring: 'Take y
ffmpeg -y -ss 00:01:09.90 -to 00:01:40.80 -i "videos/episode_003.mp4" -c copy "promo_clips/promo_rank05_ep03_30s.mp4"

# Rank #6 (Ep 2 | 36.3s): Opens with OFF-SCREEN VOICE declaring: 'You should
ffmpeg -y -ss 00:01:06.10 -to 00:01:42.40 -i "videos/episode_002.mp4" -c copy "promo_clips/promo_rank06_ep02_36s.mp4"

# Rank #7 (Ep 7 | 24.4s): Opens with GERALD declaring: 'I have enough influe
ffmpeg -y -ss 00:01:05.60 -to 00:01:30.00 -i "videos/episode_007.mp4" -c copy "promo_clips/promo_rank07_ep07_24s.mp4"

# Rank #8 (Ep 7 | 22.8s): Opens with ARISTOCRATIC WOMAN declaring: 'This is 
ffmpeg -y -ss 00:00:22.00 -to 00:00:44.80 -i "videos/episode_007.mp4" -c copy "promo_clips/promo_rank08_ep07_22s.mp4"

# Rank #9 (Ep 39 | 57.41s): Opens with LOYALIST FIGHTER declaring: 'Sleep.'
ffmpeg -y -ss 00:00:41.00 -to 00:01:38.41 -i "videos/episode_039.mp4" -c copy "promo_clips/promo_rank09_ep39_57s.mp4"

# Rank #10 (Ep 28 | 52.1s): Opens with CATHERINE declaring: 'She looks exactly
ffmpeg -y -ss 00:00:12.70 -to 00:01:04.80 -i "videos/episode_028.mp4" -c copy "promo_clips/promo_rank10_ep28_52s.mp4"

# Rank #11 (Ep 5 | 39.0s): LORD ASHCROFT: "You will not leave this church car
ffmpeg -y -ss 00:00:06.80 -to 00:00:45.80 -i "videos/episode_005.mp4" -c copy "promo_clips/promo_rank11_ep05_39s.mp4"

# Rank #12 (Ep 11 | 20.5s): JULIANA: "You have already taken enough from me. L
ffmpeg -y -ss 00:00:14.40 -to 00:00:34.90 -i "videos/episode_011.mp4" -c copy "promo_clips/promo_rank12_ep11_20s.mp4"

# Rank #13 (Ep 9 | 20.2s): BLOND NOBLEMAN: "People see ghosts whenever they w
ffmpeg -y -ss 00:01:35.30 -to 00:01:55.50 -i "videos/episode_009.mp4" -c copy "promo_clips/promo_rank13_ep09_20s.mp4"

# Rank #14 (Ep 20 | 23.7s): CATHERINE: "'Practically' is a word for beggars. I
ffmpeg -y -ss 00:00:15.40 -to 00:00:39.10 -i "videos/episode_020.mp4" -c copy "promo_clips/promo_rank14_ep20_23s.mp4"

# Rank #15 (Ep 4 | 24.3s): GERALD: "Look at him." (Mocking, Arrogant)
ffmpeg -y -ss 00:00:03.40 -to 00:00:27.70 -i "videos/episode_004.mp4" -c copy "promo_clips/promo_rank15_ep04_24s.mp4"

# Rank #16 (Ep 25 | 28.2s): ALEXANDER: "You treated her?" (Incredulous)
ffmpeg -y -ss 00:01:45.60 -to 00:02:13.80 -i "videos/episode_025.mp4" -c copy "promo_clips/promo_rank16_ep25_28s.mp4"

# Rank #17 (Ep 12 | 23.91s): CLARISSA: "Do it, and we withdraw the charges." (C
ffmpeg -y -ss 00:01:03.30 -to 00:01:27.21 -i "videos/episode_012.mp4" -c copy "promo_clips/promo_rank17_ep12_23s.mp4"

# Rank #18 (Ep 16 | 33.39s): THUG WITH CAP: "Harrington! Gerald Harrington paid
ffmpeg -y -ss 00:00:49.80 -to 00:01:23.19 -i "videos/episode_016.mp4" -c copy "promo_clips/promo_rank18_ep16_33s.mp4"

# Rank #19 (Ep 23 | 33.5s): LADY JULIANA: "Someone is poisoning her." (Cold, D
ffmpeg -y -ss 00:01:19.00 -to 00:01:52.50 -i "videos/episode_023.mp4" -c copy "promo_clips/promo_rank19_ep23_33s.mp4"

# Rank #20 (Ep 25 | 21.8s): ALEXANDER: "Worry? They struck you. They could hav
ffmpeg -y -ss 00:02:17.40 -to 00:02:39.20 -i "videos/episode_025.mp4" -c copy "promo_clips/promo_rank20_ep25_21s.mp4"

# Rank #21 (Ep 41 | 35.09s): CATHERINE: "Still arrogant. Still standing." (O.S.
ffmpeg -y -ss 00:01:01.00 -to 00:01:36.09 -i "videos/episode_041.mp4" -c copy "promo_clips/promo_rank21_ep41_35s.mp4"

# Rank #22 (Ep 5 | 45.3s): JULIANA: "Barbara, don't!" (Screaming, Desperate)
ffmpeg -y -ss 00:00:55.50 -to 00:01:40.80 -i "videos/episode_005.mp4" -c copy "promo_clips/promo_rank22_ep05_45s.mp4"

# Rank #23 (Ep 30 | 24.5s): ELDER NOBLEMAN: "You have a rat in your cellar, Ru
ffmpeg -y -ss 00:00:08.80 -to 00:00:33.30 -i "videos/episode_030.mp4" -c copy "promo_clips/promo_rank23_ep30_24s.mp4"

# Rank #24 (Ep 21 | 52.0s): PRUDENCE: "He is only seven! If you do not come, h
ffmpeg -y -ss 00:00:31.00 -to 00:01:23.00 -i "videos/episode_021.mp4" -c copy "promo_clips/promo_rank24_ep21_52s.mp4"

# Rank #25 (Ep 33 | 36.0s): LORD: "That is not what I asked." (Coldly Dismissi
ffmpeg -y -ss 00:00:34.00 -to 00:01:10.00 -i "videos/episode_033.mp4" -c copy "promo_clips/promo_rank25_ep33_36s.mp4"

# Rank #26 (Ep 44 | 35.0s): POLICE CONSTABLE: "I have more than enough." (Cold
ffmpeg -y -ss 00:00:11.40 -to 00:00:46.40 -i "videos/episode_044.mp4" -c copy "promo_clips/promo_rank26_ep44_35s.mp4"

# Rank #27 (Ep 8 | 21.8s): JULIANA: "How do you know that?" (Inquiring, Soft)
ffmpeg -y -ss 00:00:15.10 -to 00:00:36.90 -i "videos/episode_008.mp4" -c copy "promo_clips/promo_rank27_ep08_21s.mp4"

# Rank #28 (Ep 9 | 29.3s): Action: Juliana places a comforting hand over the 
ffmpeg -y -ss 00:01:08.00 -to 00:01:37.30 -i "videos/episode_009.mp4" -c copy "promo_clips/promo_rank28_ep09_29s.mp4"

# Rank #29 (Ep 11 | 27.4s): GERALD: "The last time I came here." (Cold, Certai
ffmpeg -y -ss 00:00:20.90 -to 00:00:48.30 -i "videos/episode_011.mp4" -c copy "promo_clips/promo_rank29_ep11_27s.mp4"

# Rank #30 (Ep 12 | 30.7s): ALEXANDER: "I have never touched your property." (
ffmpeg -y -ss 00:00:21.60 -to 00:00:52.30 -i "videos/episode_012.mp4" -c copy "promo_clips/promo_rank30_ep12_30s.mp4"

# Rank #31 (Ep 29 | 28.8s): CATHERINE: "You still call this a legacy?" (Cruel,
ffmpeg -y -ss 00:00:24.80 -to 00:00:53.60 -i "videos/episode_029.mp4" -c copy "promo_clips/promo_rank31_ep29_28s.mp4"

# Rank #32 (Ep 34 | 34.5s): Action: Prudence the young maid stands trembling i
ffmpeg -y -ss 00:00:41.00 -to 00:01:15.50 -i "videos/episode_034.mp4" -c copy "promo_clips/promo_rank32_ep34_34s.mp4"

# Rank #33 (Ep 42 | 24.5s): BLOND NOBLEMAN: "Guards! Arrest this imposter!" (F
ffmpeg -y -ss 00:00:18.00 -to 00:00:42.50 -i "videos/episode_042.mp4" -c copy "promo_clips/promo_rank33_ep42_24s.mp4"

# Rank #34 (Ep 43 | 36.4s): BLOND NOBLEMAN: "You're lying!" (Hysterical, Panic
ffmpeg -y -ss 00:00:00.60 -to 00:00:37.00 -i "videos/episode_043.mp4" -c copy "promo_clips/promo_rank34_ep43_36s.mp4"

# Rank #35 (Ep 41 | 28.8s): NOBLEMAN: "She actually came back to the chapel." 
ffmpeg -y -ss 00:00:31.70 -to 00:01:00.50 -i "videos/episode_041.mp4" -c copy "promo_clips/promo_rank35_ep41_28s.mp4"

# Rank #36 (Ep 6 | 20.9s): MYSTERIOUS BEARDED MAN: "Yes." (Low)
ffmpeg -y -ss 00:00:28.10 -to 00:00:49.00 -i "videos/episode_006.mp4" -c copy "promo_clips/promo_rank36_ep06_20s.mp4"

# Rank #37 (Ep 6 | 31.7s): Action: Instead of stopping her, the Mysterious Be
ffmpeg -y -ss 00:01:14.30 -to 00:01:46.00 -i "videos/episode_006.mp4" -c copy "promo_clips/promo_rank37_ep06_31s.mp4"

# Rank #38 (Ep 4 | 40.2s): JULIANA: "Then I accept." (Resolved)
ffmpeg -y -ss 00:01:12.80 -to 00:01:53.00 -i "videos/episode_004.mp4" -c copy "promo_clips/promo_rank38_ep04_40s.mp4"

# Rank #39 (Ep 15 | 28.7s): BALD THUG: "Look at her! Crying over weeds!" (Crue
ffmpeg -y -ss 00:00:57.30 -to 00:01:26.00 -i "videos/episode_015.mp4" -c copy "promo_clips/promo_rank39_ep15_28s.mp4"

# Rank #40 (Ep 18 | 34.0s): ALEXANDER: "Someone wanted us out." (Cold, Ominous
ffmpeg -y -ss 00:02:38.00 -to 00:03:12.00 -i "videos/episode_018.mp4" -c copy "promo_clips/promo_rank40_ep18_34s.mp4"

# Rank #41 (Ep 20 | 24.85s): CATHERINE: "Let the peasants rot in their barns." 
ffmpeg -y -ss 00:01:29.90 -to 00:01:54.75 -i "videos/episode_020.mp4" -c copy "promo_clips/promo_rank41_ep20_24s.mp4"

# Rank #42 (Ep 16 | 31.7s): THUG WITH CAP: "Move aside, soldier." (Menacing, G
ffmpeg -y -ss 00:00:02.10 -to 00:00:33.80 -i "videos/episode_016.mp4" -c copy "promo_clips/promo_rank42_ep16_31s.mp4"

# Rank #43 (Ep 32 | 22.8s): CATHERINE: "Silence! Silence!" (Hysterical, Scream
ffmpeg -y -ss 00:01:59.60 -to 00:02:22.40 -i "videos/episode_032.mp4" -c copy "promo_clips/promo_rank43_ep32_22s.mp4"

# Rank #44 (Ep 36 | 47.25s): ALEXANDER'S MOTHER: "Two days from now." (Deadly S
ffmpeg -y -ss 00:02:33.50 -to 00:03:20.75 -i "videos/episode_036.mp4" -c copy "promo_clips/promo_rank44_ep36_47s.mp4"

# Rank #45 (Ep 46 | 31.7s): HIGH PRIEST: "None shall leave until every witness
ffmpeg -y -ss 00:00:17.30 -to 00:00:49.00 -i "videos/episode_046.mp4" -c copy "promo_clips/promo_rank45_ep46_31s.mp4"

# Rank #46 (Ep 24 | 27.2s): NOBLEWOMAN: "Every stone. Perhaps when your hands 
ffmpeg -y -ss 00:00:57.80 -to 00:01:25.00 -i "videos/episode_024.mp4" -c copy "promo_clips/promo_rank46_ep24_27s.mp4"

# Rank #47 (Ep 23 | 51.8s): LADY JULIANA: "Her mouth is terribly dry." (Solemn
ffmpeg -y -ss 00:00:24.00 -to 00:01:15.80 -i "videos/episode_023.mp4" -c copy "promo_clips/promo_rank47_ep23_51s.mp4"

# Rank #48 (Ep 26 | 39.1s): JULIANA: "Rest now, Your Grace. You are safe tonig
ffmpeg -y -ss 00:00:40.30 -to 00:01:19.40 -i "videos/episode_026.mp4" -c copy "promo_clips/promo_rank48_ep26_39s.mp4"

# Rank #49 (Ep 30 | 37.8s): RUPERT: "She knows the Duchess was poisoned." (Mut
ffmpeg -y -ss 00:00:26.50 -to 00:01:04.30 -i "videos/episode_030.mp4" -c copy "promo_clips/promo_rank49_ep30_37s.mp4"

# Rank #50 (Ep 10 | 30.1s): ALEXANDER: "It is only a scratch." (Low, Defiant)
ffmpeg -y -ss 00:00:23.20 -to 00:00:53.30 -i "videos/episode_010.mp4" -c copy "promo_clips/promo_rank50_ep10_30s.mp4"

# Rank #51 (Ep 15 | 42.7s): THUG WITH CAP: "We're clearing this rubbish." (Moc
ffmpeg -y -ss 00:00:13.00 -to 00:00:55.70 -i "videos/episode_015.mp4" -c copy "promo_clips/promo_rank51_ep15_42s.mp4"

# Rank #52 (Ep 18 | 40.2s): JULIANA: "The window!" (Urgent, Shouting)
ffmpeg -y -ss 00:01:43.80 -to 00:02:24.00 -i "videos/episode_018.mp4" -c copy "promo_clips/promo_rank52_ep18_40s.mp4"

# Rank #53 (Ep 21 | 28.8s): PRUDENCE: "Lady Juliana! Please! You have to help 
ffmpeg -y -ss 00:00:04.20 -to 00:00:33.00 -i "videos/episode_021.mp4" -c copy "promo_clips/promo_rank53_ep21_28s.mp4"

# Rank #54 (Ep 24 | 31.0s): NOBLEWOMAN: "You thought? A new maid thinks she kn
ffmpeg -y -ss 00:00:22.50 -to 00:00:53.50 -i "videos/episode_024.mp4" -c copy "promo_clips/promo_rank54_ep24_31s.mp4"

# Rank #55 (Ep 28 | 29.4s): CATHERINE: "How convenient that the only person wh
ffmpeg -y -ss 00:01:01.60 -to 00:01:31.00 -i "videos/episode_028.mp4" -c copy "promo_clips/promo_rank55_ep28_29s.mp4"

# Rank #56 (Ep 37 | 32.4s): CATHERINE: "Juliana's execution comes after the we
ffmpeg -y -ss 00:00:23.80 -to 00:00:56.20 -i "videos/episode_037.mp4" -c copy "promo_clips/promo_rank56_ep37_32s.mp4"

# Rank #57 (Ep 45 | 20.0s): ALEXANDER: "You poisoned my mother. You tortured m
ffmpeg -y -ss 00:00:54.00 -to 00:01:14.00 -i "videos/episode_045.mp4" -c copy "promo_clips/promo_rank57_ep45_20s.mp4"

# Rank #58 (Ep 31 | 37.0s): CATHERINE: "No. You became a disgrace when Gerald 
ffmpeg -y -ss 00:00:43.20 -to 00:01:20.20 -i "videos/episode_031.mp4" -c copy "promo_clips/promo_rank58_ep31_37s.mp4"

# Rank #59 (Ep 8 | 21.3s): JULIANA: "Some of the pages are ruined. Careful." 
ffmpeg -y -ss 00:00:00.20 -to 00:00:21.50 -i "videos/episode_008.mp4" -c copy "promo_clips/promo_rank59_ep08_21s.mp4"

# Rank #60 (Ep 14 | 51.83s): ALEXANDER: "You should never have had to bleed for
ffmpeg -y -ss 00:00:35.80 -to 00:01:27.63 -i "videos/episode_014.mp4" -c copy "promo_clips/promo_rank60_ep14_51s.mp4"

# Rank #61 (Ep 19 | 26.0s): ELDER VILLAGER: "You saved my son's life." (Warm, 
ffmpeg -y -ss 00:00:23.20 -to 00:00:49.20 -i "videos/episode_019.mp4" -c copy "promo_clips/promo_rank61_ep19_26s.mp4"

# Rank #62 (Ep 10 | 25.0s): ALEXANDER: "Not much." (Gruff)
ffmpeg -y -ss 00:00:54.00 -to 00:01:19.00 -i "videos/episode_010.mp4" -c copy "promo_clips/promo_rank62_ep10_25s.mp4"

# Rank #63 (Ep 22 | 20.0s): HOUSEKEEPER: "She looks soft." (Cold, Skeptical)
ffmpeg -y -ss 00:00:49.50 -to 00:01:09.50 -i "videos/episode_022.mp4" -c copy "promo_clips/promo_rank63_ep22_20s.mp4"

# Rank #64 (Ep 32 | 31.6s): CATHERINE: "A disgraced woman?" (Sneering, Mocking
ffmpeg -y -ss 00:00:47.80 -to 00:01:19.40 -i "videos/episode_032.mp4" -c copy "promo_clips/promo_rank64_ep32_31s.mp4"

# Rank #65 (Ep 34 | 23.6s): LORD: "She calls it healing." (Mocking, Smug)
ffmpeg -y -ss 00:01:48.00 -to 00:02:11.60 -i "videos/episode_034.mp4" -c copy "promo_clips/promo_rank65_ep34_23s.mp4"

# Rank #66 (Ep 36 | 30.0s): ALEXANDER: "Then where is she?" (Desperate)
ffmpeg -y -ss 00:01:36.80 -to 00:02:06.80 -i "videos/episode_036.mp4" -c copy "promo_clips/promo_rank66_ep36_30s.mp4"

# Rank #67 (Ep 47 | 38.3s): CATHERINE: "I have nowhere to go, Your Grace." (De
ffmpeg -y -ss 00:01:00.50 -to 00:01:38.80 -i "videos/episode_047.mp4" -c copy "promo_clips/promo_rank67_ep47_38s.mp4"

# Rank #68 (Ep 22 | 35.0s): Action: Prudence rushes into frame, grabbing Julia
ffmpeg -y -ss 00:01:36.00 -to 00:02:11.00 -i "videos/episode_022.mp4" -c copy "promo_clips/promo_rank68_ep22_35s.mp4"

# Rank #69 (Ep 46 | 49.2s): HIGH PRIEST: "Careful, girl. You mistake my patien
ffmpeg -y -ss 00:01:29.30 -to 00:02:18.50 -i "videos/episode_046.mp4" -c copy "promo_clips/promo_rank69_ep46_49s.mp4"

# Rank #70 (Ep 14 | 36.5s): JULIANA: "Now release my husband." (Firm, Commandi
ffmpeg -y -ss 00:00:10.50 -to 00:00:47.00 -i "videos/episode_014.mp4" -c copy "promo_clips/promo_rank70_ep14_36s.mp4"

# Rank #71 (Ep 17 | 22.2s): JULIANA: "Some of them survived." (Soft, Emotional
ffmpeg -y -ss 00:00:09.30 -to 00:00:31.50 -i "videos/episode_017.mp4" -c copy "promo_clips/promo_rank71_ep17_22s.mp4"

# Rank #72 (Ep 27 | 39.1s): LADY CATHERINE: "Who permitted you to give medicin
ffmpeg -y -ss 00:01:18.10 -to 00:01:57.20 -i "videos/episode_027.mp4" -c copy "promo_clips/promo_rank72_ep27_39s.mp4"

# Rank #73 (Ep 31 | 20.4s): CATHERINE: "You call that marriage?" (Incredulous,
ffmpeg -y -ss 00:01:17.80 -to 00:01:38.20 -i "videos/episode_031.mp4" -c copy "promo_clips/promo_rank73_ep31_20s.mp4"

# Rank #74 (Ep 50 | 52.8s): CATHERINE: "That's not absolution, Thomas. That's 
ffmpeg -y -ss 00:00:27.20 -to 00:01:20.00 -i "videos/episode_050.mp4" -c copy "promo_clips/promo_rank74_ep50_52s.mp4"

# Rank #75 (Ep 27 | 38.1s): JULIANA: "He is a soldier. A veteran from the Peni
ffmpeg -y -ss 00:00:13.40 -to 00:00:51.50 -i "videos/episode_027.mp4" -c copy "promo_clips/promo_rank75_ep27_38s.mp4"

# Rank #76 (Ep 29 | 23.9s): JULIANA: "My husband will find me." (Steely, Resol
ffmpeg -y -ss 00:01:09.80 -to 00:01:33.70 -i "videos/episode_029.mp4" -c copy "promo_clips/promo_rank76_ep29_23s.mp4"

# Rank #77 (Ep 40 | 43.18s): ROYAL GUARD: "Every one, my Lord." (Obedient, Firm
ffmpeg -y -ss 00:01:06.90 -to 00:01:50.08 -i "videos/episode_040.mp4" -c copy "promo_clips/promo_rank77_ep40_43s.mp4"

# Rank #78 (Ep 13 | 21.6s): CLARISSA: "Careful, sister." (O.S.) (Mocking, Vind
ffmpeg -y -ss 00:00:37.00 -to 00:00:58.60 -i "videos/episode_013.mp4" -c copy "promo_clips/promo_rank78_ep13_21s.mp4"

# Rank #79 (Ep 13 | 22.8s): ALEXANDER: "I would rather face the gallows than w
ffmpeg -y -ss 00:00:24.20 -to 00:00:47.00 -i "videos/episode_013.mp4" -c copy "promo_clips/promo_rank79_ep13_22s.mp4"

# Rank #80 (Ep 33 | 28.5s): MAID: "Please, my Lord... he is only seven!" (Begg
ffmpeg -y -ss 00:01:09.50 -to 00:01:38.00 -i "videos/episode_033.mp4" -c copy "promo_clips/promo_rank80_ep33_28s.mp4"

# Rank #81 (Ep 40 | 25.7s): LORD HARRINGTON: "This place has always been unluc
ffmpeg -y -ss 00:00:30.10 -to 00:00:55.80 -i "videos/episode_040.mp4" -c copy "promo_clips/promo_rank81_ep40_25s.mp4"

# Rank #82 (Ep 43 | 30.7s): BLOND NOBLEMAN: "You have all been deceived!" (Des
ffmpeg -y -ss 00:00:24.10 -to 00:00:54.80 -i "videos/episode_043.mp4" -c copy "promo_clips/promo_rank82_ep43_30s.mp4"

# Rank #83 (Ep 45 | 23.9s): JULIANA: "All this time?" (Incredulous, Moved)
ffmpeg -y -ss 00:00:27.60 -to 00:00:51.50 -i "videos/episode_045.mp4" -c copy "promo_clips/promo_rank83_ep45_23s.mp4"

# Rank #84 (Ep 48 | 23.3s): CATHERINE: "Good. Let them remember it." (Spiteful
ffmpeg -y -ss 00:00:37.30 -to 00:01:00.60 -i "videos/episode_048.mp4" -c copy "promo_clips/promo_rank84_ep48_23s.mp4"

# Rank #85 (Ep 37 | 26.3s): Action: Juliana curls her fingers back, pulling aw
ffmpeg -y -ss 00:01:33.50 -to 00:01:59.80 -i "videos/episode_037.mp4" -c copy "promo_clips/promo_rank85_ep37_26s.mp4"

# Rank #86 (Ep 35 | 35.5s): ALEXANDER'S MOTHER: "Then why did they never tell 
ffmpeg -y -ss 00:02:02.00 -to 00:02:37.50 -i "videos/episode_035.mp4" -c copy "promo_clips/promo_rank86_ep35_35s.mp4"

# Rank #87 (Ep 35 | 20.0s): ALEXANDER'S MOTHER: "Then how did you survive?" (S
ffmpeg -y -ss 00:01:11.50 -to 00:01:31.50 -i "videos/episode_035.mp4" -c copy "promo_clips/promo_rank87_ep35_20s.mp4"

# Rank #88 (Ep 38 | 25.11s): JULIANA: "I will not betray him." (Resolute)
ffmpeg -y -ss 00:01:02.80 -to 00:01:27.91 -i "videos/episode_038.mp4" -c copy "promo_clips/promo_rank88_ep38_25s.mp4"

# Rank #89 (Ep 17 | 22.2s): ALEXANDER: "For what?" (Gruff, Low)
ffmpeg -y -ss 00:00:16.80 -to 00:00:39.00 -i "videos/episode_017.mp4" -c copy "promo_clips/promo_rank89_ep17_22s.mp4"

# Rank #90 (Ep 38 | 28.0s): JULIANA: "What if I die here?" (Fearful, Pleading)
ffmpeg -y -ss 00:00:45.50 -to 00:01:13.50 -i "videos/episode_038.mp4" -c copy "promo_clips/promo_rank90_ep38_28s.mp4"

# Rank #91 (Ep 47 | 31.2s): CATHERINE: "You want me? As a guest?" (Incredulous
ffmpeg -y -ss 00:01:36.00 -to 00:02:07.20 -i "videos/episode_047.mp4" -c copy "promo_clips/promo_rank91_ep47_31s.mp4"

# Rank #92 (Ep 19 | 20.3s): ALEXANDER: "My mother is a prisoner in her own hou
ffmpeg -y -ss 00:01:16.50 -to 00:01:36.80 -i "videos/episode_019.mp4" -c copy "promo_clips/promo_rank92_ep19_20s.mp4"

# Rank #93 (Ep 44 | 21.2s): CATHERINE: "I was supposed to be your Duchess!" (D
ffmpeg -y -ss 00:00:46.60 -to 00:01:07.80 -i "videos/episode_044.mp4" -c copy "promo_clips/promo_rank93_ep44_21s.mp4"

# Rank #94 (Ep 48 | 30.8s): Action: Catherine, adorned in an ornate dark burgu
ffmpeg -y -ss 00:00:00.00 -to 00:00:30.80 -i "videos/episode_048.mp4" -c copy "promo_clips/promo_rank94_ep48_30s.mp4"

# Rank #95 (Ep 49 | 28.6s): CATHERINE: "Second, I want to know what the counci
ffmpeg -y -ss 00:01:24.20 -to 00:01:52.80 -i "videos/episode_049.mp4" -c copy "promo_clips/promo_rank95_ep49_28s.mp4"

# Rank #96 (Ep 26 | 23.5s): DOWAGER DUCHESS: "Your hand... Let me see your han
ffmpeg -y -ss 00:01:36.00 -to 00:01:59.50 -i "videos/episode_026.mp4" -c copy "promo_clips/promo_rank96_ep26_23s.mp4"

# Rank #97 (Ep 49 | 25.7s): CATHERINE: "Good. That's what I pay her for." (Ple
ffmpeg -y -ss 00:00:15.80 -to 00:00:41.50 -i "videos/episode_049.mp4" -c copy "promo_clips/promo_rank97_ep49_25s.mp4"

# Rank #98 (Ep 50 | 27.4s): CATHERINE: "Then let's stop pretending this was on
ffmpeg -y -ss 00:00:12.00 -to 00:00:39.40 -i "videos/episode_050.mp4" -c copy "promo_clips/promo_rank98_ep50_27s.mp4"

# Rank #99 (Ep 42 | 23.5s): BLOND NOBLEMAN: "You cannot be him. Alexander died
ffmpeg -y -ss 00:00:30.50 -to 00:00:54.00 -i "videos/episode_042.mp4" -c copy "promo_clips/promo_rank99_ep42_23s.mp4"

# Rank #100 (Ep 39 | 22.7s): Action: Four royal guards in red ceremonial tunics
ffmpeg -y -ss 00:00:13.80 -to 00:00:36.50 -i "videos/episode_039.mp4" -c copy "promo_clips/promo_rank100_ep39_22s.mp4"
