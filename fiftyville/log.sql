-- Keep a log of any SQL queries you execute as you solve the mystery.
-- Check info based on already known date and place
SELECT * FROM crime_scene_reports WHERE month = 7 AND day = 28 AND street = 'Humphrey Street';
-- Check corresponding interviews on that day
SELECT * FROM interviews WHERE month =7 AND day = 28 AND street = 'Humphrey Street';
/*
| 161 | Ruth    | 2024 | 7     | 28  |
Sometime within ten minutes of the theft, I saw the thief get into a car in the bakery parking lot and drive away. If you have security
footage from the bakery parking lot, you might want to look for cars that left the parking lot in that time frame.                                                          |
| 162 | Eugene  | 2024 | 7     | 28  |
I don't know the thief's name, but it was someone I recognized. Earlier this morning, before I arrived at Emma's bakery,
I was walking by the ATM on Leggett Street and saw the thief there withdrawing some money.                                                                                                 |
| 163 | Raymond | 2024 | 7     | 28  |
As the thief was leaving the bakery, they called someone who talked to them for less than a minute. In the call, I heard the thief say that they were
planning to take the earliest flight out of Fiftyville tomorrow. The thief then asked the person on the other end of the phone to purchase the flight ticket. |

From interviews some new info is drawn:
1.the thief left the bakery by car in the parking lot, in need of queries about bakery_security_logs
2.Earlier that morning the theif withdrew some money at the ATM on Leggett Street, in need of queries about atm_transactions
3.The theif phoned someone to ask him to purchase the flight ticket of the earliest flight out of fiftyville on 29, Jul.
*/
SELECT * FROM bakery_security_logs WHERE hour = 10 AND minute >=15 AND minute <=25 ORDER BY minute ASC;
/*now we get possible license plate from which we can find corresponding id of people*/
SELECT * FROM atm_transactions WHERE atm_location = 'Leggett Street' AND month=7 AND day=28;
-- we get accout numbers from which we can find corresponding person id in bank accounts table.
SELECT person_id
  FROM bank_accounts
 WHERE account_number
    IN
       (SELECT account_number
          FROM atm_transactions
         WHERE atm_location = 'Leggett Street'
           AND month=7
           AND day=28);
SELECT * FROM phone_calls WHERE month = 7 AND day = 28;
-- Find the id of the airport in Fiftyvill:8
SELECT * FROM airports;
-- Find info of the earliest flight out of Fiftyville
SELECT * FROM flights WHERE origin_airport_id = 8 AND day = 29 ORDER BY hour ASC, minute ASC LIMIT 1;
-- After getting the flight id we can search for passport numbers of corresponding passengers
SELECT passport_number FROM passengers WHERE flight_id = 36;
-- Now we just need to find the person who at the same time satisfies the account_number, passport_num and license_plate we got.
SELECT  *
  FROM people
 WHERE id IN (SELECT person_id
                FROM bank_accounts
               WHERE account_number IN
                                        (SELECT account_number
                                          FROM atm_transactions
                                          WHERE atm_location = 'Leggett Street'
                                            AND month=7
                                            AND day=28))
   AND passport_num IN (SELECT passport_number FROM passengers WHERE flight_id = 36)
   AND license_plate IN (SELECT license_plate FROM bakery_security_logs WHERE hour = 10 AND minute >=15 AND minute <=25 ORDER BY minute ASC);
/*
now we have
+--------+-------+----------------+-----------------+---------------+
|   id   | name  |  phone_number  | passport_number | license_plate |
+--------+-------+----------------+-----------------+---------------+
| 467400 | Luca  | (389) 555-5198 | 8496433585      | 4328GD8       |
| 686048 | Bruce | (367) 555-5533 | 5773159633      | 94KL13X       |
+--------+-------+----------------+-----------------+---------------+
*/
--now we go to find who is the caller also the thief:
SELECT * FROM phone_calls WHERE month = 7 AND day = 28 AND caller IN('(389) 555-5198','(367) 555-5533') AND duration < 60;
/*
Final answer:
+-----+----------------+----------------+------+-------+-----+----------+
| id  |     caller     |    receiver    | year | month | day | duration |
+-----+----------------+----------------+------+-------+-----+----------+
| 233 | (367) 555-5533 | (375) 555-8161 | 2024 | 7     | 28  | 45       |
+-----+----------------+----------------+------+-------+-----+----------+
*/
