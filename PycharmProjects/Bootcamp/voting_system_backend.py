import tkinter
import pyttsx3 as tts
import speech_recognition as sr
import mysql.connector as mc
from text2digits import text2digits as ttd
from datetime import date, time, datetime
from tkinter import *
from PIL import Image, ImageTk


def connect_to_db():
    conn = mc.connect(host="localhost", password="", user="root", database="voting_system")
    return conn


def initiate():
    StartVotingSystem(date.today())


def message(msg):
    engine = tts.init()
    engine.setProperty('rate', 150)
    engine.say(msg)
    engine.runAndWait()


def start_program():
    interface = Interface()


class Interface:
    # __instance = None

    # def __new__(cls):
    #     if cls.__instance is None:
    #         return object.__new__(cls)
    #     else:
    #         return object.__new__(cls)

    def __init__(self):
        self.mainScreen = tkinter.Tk()
        self.mainScreen.title("Visually Impaired Voting System")
        self.mainScreen.geometry("1920x1080")
        self.mainScreen.configure(background="black")
        ico = Image.open('../icon.png')
        photo = ImageTk.PhotoImage(ico)
        self.mainScreen.wm_iconphoto(False, photo)
        self.mainScreenFrame = Frame(self.mainScreen, width=900, height=500, borderwidth=5, bg="purple")
        self.mainScreenFrame.place(relx=0.29, rely=0.2)
        self.mainScreenLabel = Label(master=self.mainScreenFrame, text="Press the button to initialize the system",
                                     fg="White", bg="purple", font=("Times New Roman", 30, "bold"))
        self.mainScreenLabel.place(rely=0.2, relx=0.13)
        self.mainScreenBtn = Button(master=self.mainScreenFrame, text="Initiate System", bg="Blue", fg="white", borderwidth=2,
                                    command=initiate, font=("Times New Roman", 30, "bold"))
        self.mainScreenBtn.place(relx=0.33, rely=0.4)
        self.mainScreen.mainloop()

    def configure_widgets(self, text):
        self.mainScreenLabel.configure(text=text)
        self.mainScreenBtn.destroy()


class Voter:
    # voter class created to make sure no user with the same voters id number will cast a vote two times
    def __init__(self):
        # super().__init__()
        # self.configure_widgets("REGISTERING VOTER'S IDENTIFICATION NUMBER INTO DATABASE...")
        self.connection = connect_to_db()
        self.cursor = self.connection.cursor()
        self.votersId = ""
        self.get_voters_id()
        self.already_voted = False

    def get_voters_id(self):
        message("Welcome.")
        message("You're required to provide your voter's identification number before you can partake in the election")
        message("Please mention your voter's identification number")
        message("System listening...")
        engine = sr.Recognizer()
        with sr.Microphone() as source:
            audio = engine.listen(source)
            try:
                idNumber = engine.recognize_google(audio)
                convertedNumber = ttd.Text2Digits()
                idNumber = convertedNumber.convert(idNumber)
                self.votersId = idNumber
                # check whether the voters id mentioned already exists in the database
                # if it exists then the user has already voted before
                # and so will not be allowed to vote again
                registered = self.register_voters_id_into_database()
                if registered:
                    message("You have now been validated and as a result, you can participate in the election")
                    message("Please be aware that you will be able to vote only once")
                print(f"Voter's Identification Number: {idNumber}")
            except sr.UnknownValueError:
                message("System failed to recognize your voters identification number")
                message("Please try again")
                self.get_voters_id()
            except sr.RequestError:
                message("System down at the moment")
                message("Rebooting....")
                self.get_voters_id()

    def register_voters_id_into_database(self):
        # we check whether voters identification number already exists in the database
        stmt = "SELECT voters_id FROM voters WHERE voters_id = %s"
        self.cursor.execute(stmt, (self.votersId,))
        result = self.cursor.fetchall()
        # if it doesn't exist then we add it and return true meaning it has been registered in the database
        if len(result) == 0:
            stmt = "INSERT INTO voters VALUES(%s)"
            self.cursor.execute(stmt, (self.votersId,))
            self.connection.commit()
            return True
        # if false we return false meaning it hasn't been registered in the database
        else:
            message("Access denied")
            message("You are have already casted a vote")
            self.already_voted = True
            return False


class StartVotingSystem:
    def __init__(self, today):
        self.startTime = time(hour=8, minute=0, second=0)
        self.startDay = today
        self.endTime = time(hour=19, minute=30, second=0)
        # this variable is to check whether the system has been run or not
        # to prevent any un-for-seen errors
        self.runVotingSystem = False
        # the system will start on the day we access it
        if date.today() != self.startDay:
            message("Sorry the system has not been made accessible on this day")
            message("Kindly wait to access it on the day specified in the news")
        else:
            currentTime = datetime.now().time()
            # the time for the system to start is 8 AM and so if the current time is lower than the specified time
            # don't allow access to the system
            if currentTime < self.startTime:
                message("System is not yet initiated, comeback when it's 8 AM")
            else:
                # included for the program to run until a specified time
                while currentTime < self.endTime:
                    self.initialize_system = VotingSystem()
                    currentTime = datetime.now().time()
                    self.runVotingSystem = True
                    # included for testing purposes when the system goes into use, will be removed
                    break
                if self.runVotingSystem:
                    message("Election has ended")
                    self.initialize_system.declare_winner()
                else:
                    message("You arrived late to the election.")
                    message("The election has already taken place")
                # we always want to delete the voters id record in the voters table so that when people
                # want to vote for candidates in different category of elections, they can partake
                self.connection = connect_to_db()
                self.cursor = self.connection.cursor()
                stmt = "DELETE FROM voters "
                self.cursor.execute(stmt)
                self.connection.commit()
        return


class VotingSystem:

    def __init__(self):
        # super().__init__()
        # self.configure_widgets("WELCOME TO THE VOTING INTERFACE")
        # connecting to the database and initializing the system
        self.conn = connect_to_db()
        self.cursor = self.conn.cursor()
        # sql to get the number of candidates to take part in the election
        sql = "SELECT COUNT(Identifier) FROM candidates"
        self.cursor.execute(sql)
        number = self.cursor.fetchall()
        self.candidatesNumber = number[0][0]
        # candidates would be a variable to hold all the candidates in the election
        self.candidates = []
        for index in range(1,  self.candidatesNumber + 1):
            self.candidates.append({f"Candidate {index}": "none"})
        self.fetch_candidate(c_ids=self.candidatesNumber + 1)
        self.voter = Voter()
        if self.voter.already_voted:
            return
        self.announce_candidates()

    def fetch_candidate(self, c_ids):
        # results variable holds the details of the candidates in the database
        # needed for the system to be able to mention the current candidates for the voter to make a decision
        # as to who to vote for
        results = []
        for ids in range(1, c_ids + 1):
            stmt = "SELECT Identifier, Name, Party FROM candidates WHERE Identifier = %s"
            self.cursor.execute(stmt, (ids,))
            results.append(self.cursor.fetchall())
        j = 1
        for index in range(0, len(results) - 1):
            self.candidates[index][f"Candidate {j}"] = {"Number": results[index][0][0], "Name": results[index][0][1],
                                                        "Party": results[index][0][2]}
            j += 1

    def announce_candidates(self):
        # self.configure_widgets("MENTIONING CANDIDATES....")
        message("The candidates for the election being held are: ")
        engine = tts.init()
        engine.setProperty("rate", 150)
        i = 1
        for candidate in self.candidates:
            engine.say(f"Candidate Number: {candidate[f'Candidate {i}']['Number']}")
            engine.say(f"Candidate Name: {candidate[f'Candidate {i}']['Name']}")
            engine.say(f"Candidate Party: {candidate[f'Candidate {i}']['Party']}")
            if candidate[f'Candidate {i}']['Number'] != self.candidatesNumber:
                engine.say("Next...")
            engine.runAndWait()
            i += 1
        message("Say ready when you're set to cast your vote.")
        response = self.listen_for_ready()
        while response != "ready":
            message("Didn't quite get that")
            message("System ready for your request again")
            response = self.listen_for_ready()
        self.cast_vote()

    def listen_for_ready(self):
        # self.configure_widgets("WAITING FOR READY SIGNAL TO ALLOW A VOTER CAST VOTE....")
        message("listening...")
        engine = sr.Recognizer()
        with sr.Microphone() as source:
            audio = engine.listen(source)
            try:
                response = engine.recognize_google(audio)
                return response
            except sr.UnknownValueError:
                self.listen_for_ready()
            except sr.RequestError:
                message("Refreshing the system...")
                self.announce_candidates()

    def cast_vote(self):
        # self.configure_widgets("VOTER CASTING VOTE...")
        message("Please provide the system with the number corresponding to the candidate you wish to vote for")
        message("System ready to receive your vote now")
        message("listening...")
        engine = sr.Recognizer()
        with sr.Microphone() as source:
            audio = engine.listen(source)
            try:
                vote = engine.recognize_google(audio)
                # sliced because voter will have to respond with number followed by the actual digit, and we want to
                # collect only the digit value
                vote = vote[7:]
                # used because the return from the speech recognition would be in a string word form on the number,
                # and we would need to convert to the digit form
                digitVersionOfVote = ttd.Text2Digits()
                # value returned from the text to digits is a string, and we need to convert it to int to make some
                # conditions work
                vote = int(digitVersionOfVote.convert(vote))
                # to check for voters who might cast votes for unrecognized candidates
                if vote > self.candidatesNumber:
                    message("Your ballot has been rejected")
                    message("You selected a candidate that does not exist")
                    return
                oldVoteNum = self.fetch_current_vote_num(vote)
                self.record_vote(vote)
                newVoteNum = self.fetch_current_vote_num(vote)
                # indicates that the voter's vote has been recorded successfully into the database
                if newVoteNum > oldVoteNum:
                    message("Vote recorded...")
                    message("Thank you for participating in this election...")
                    message("Enjoy the rest of your day.")
                    return
                else:
                    message("An error occurred while registering your vote")
                    message("Please try again")
                    self.cast_vote()
            except sr.UnknownValueError:
                message("Sorry, I did not get your vote")
                message("Please try again")
                self.cast_vote()
            except sr.RequestError:
                message("System experienced an unexpected downtime")
                message("Re-booting...")
                self.announce_candidates()

    def record_vote(self, number):
        # self.configure_widgets("VOTE RECORDED")
        # added to be updating the votes column in the database anytime a voter casts a vote
        currentVote = self.fetch_current_vote_num(number)
        sql = "UPDATE candidates SET Votes = %s WHERE Identifier = %s"
        self.cursor.execute(sql, (currentVote + 1, number, ))
        self.conn.commit()

    def fetch_current_vote_num(self, identifier):
        # function included to provide the possibility to check whether a new vote has been added successfully or not
        stmt = "SELECT Votes FROM candidates WHERE Identifier = %s"
        self.cursor.execute(stmt, (identifier,))
        currentVote = self.cursor.fetchall()
        currentVote = currentVote[0][0]
        return currentVote

    def declare_winner(self):
        stmt = "SELECT MAX(Votes) FROM candidates"
        self.cursor.execute(stmt)
        highestVote = self.cursor.fetchall()
        highestVote = highestVote[0][0]
        # this sql query provides functionality for checking whether there was a draw or not
        stmt = "SELECT Name, Party, Votes FROM candidates WHERE Votes = %s"
        self.cursor.execute(stmt, (highestVote,))
        info = self.cursor.fetchall()
        if len(info) > 1:
            message("Candidates")
            for candidate in range(0, len(info)):
                message(f"{info[candidate][0]} of the {info[candidate][1]}, ")
            message("Have tied in the election")
        else:
            winner = info[0][0]
            party = info[0][1]
            votes = info[0][2]
            message(f"{winner} of the {party} has won the election with {votes} votes.")


start_program()
