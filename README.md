# Calorie-Calculator-API
********
**Description**
This is a contained API to demonstrate how I will implement this API in my full-stack health app. It is a working app and can run tests to verify that the values are correct. This is a key part of my app, however I don't know how long
that project will take me so I want to post my smaller condensed projects on my github before I am finished with the app as a whole. The calculations are correct and I will be re-using this code for my app.
********
# TLDR
**NOT A SECURE SERVICE**
In my real app I would not be sending over user_id's instead I would use token, however for just working on this project user_id's worked better. 
********
# Functionality
********
calorie_warnings: A simple print function to display warnings if a users calories are considered low, or dangerously low according to resources online

kg_to_lbs, lbs_to_kg: simple conversion functions mainly for personal use as I am from the US but many of the formulas work with kgs

calculate_bmr: Calculates someones base metabolic rate which is just the amount of calories someone would burn if they did absolutely nothin all day

calculate_tdee: Calculates someones total daily energy expenditure, which is an estimate to how many calories someone burns based on their activity level

calculate_calories: Based on timeframe in days reccomend the amount of calories to eat each day. It is estimated that a pound of weight equivalates approximately 3500 calories, using
                    this we can find how many total calories are required to go from current weight to goal weight. Then we can calculate the amount of calories to be consumed each day
                    to reach target weight within timeframe.

daily_checkin: Adds a daily entry of weight to a user's weight_check list, then will check if this weight check is the start of a new week of entries. If it is, then go back two weeks
                and see how much weight has shifted in that time.

weekly_check: Works with daily_checkin, and is called if the entry is divisible by 7, working if a user enters weight each day. If it is an entry number divisible by 7 then see if the users
              weight has stagnated. IE: if the user is trying to lose weight but has either gained weight or failed to lose 2 or more pounds over the last 2 weeks, and vice versa. If so
              ask the user if they wish to lower their calories by 200, and if so set calories to be lower.
********
# Use
This is a key component to my activity-app and will serve as the basis for user creation and real progress. It will need to be slightly altered when implementing with my app, however the majority
of its functionality works well and will be used in my app.