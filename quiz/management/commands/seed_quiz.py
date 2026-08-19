from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question

class Command(BaseCommand):
    help = 'Seeds the database with a default quiz and 50 general knowledge questions'

    def handle(self, *args, **kwargs):
        # Create or update default Quiz
        quiz, created = Quiz.objects.get_or_create(
            id=1,
            defaults={
                'title': 'General Knowledge Ultimate Quiz',
                'description': 'A quiz containing 50 diverse questions. Every time you start, you will get 10 random unique questions!'
            }
        )
        if not created:
            self.stdout.write("Quiz already exists, clearing previous questions to reseed...")
            Question.objects.filter(quiz=quiz).delete()
        else:
            self.stdout.write("Created new quiz: General Knowledge Ultimate Quiz")

        # Define 50 questions
        questions_data = [
            ("What is the capital of France?", "London", "Paris", "Rome", "Berlin", 2),
            ("Which planet is known as the Red Planet?", "Earth", "Mars", "Jupiter", "Venus", 2),
            ("Who wrote 'Romeo and Juliet'?", "Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain", 2),
            ("What is the largest ocean on Earth?", "Atlantic Ocean", "Indian Ocean", "Pacific Ocean", "Arctic Ocean", 3),
            ("What is the chemical symbol for gold?", "Go", "Au", "Ag", "Gd", 2),
            ("How many continents are there on Earth?", "5", "6", "7", "8", 3),
            ("Which is the tallest mountain in the world?", "K2", "Mount Everest", "Mount Kilimanjaro", "Denali", 2),
            ("What is the square root of 64?", "6", "7", "8", "9", 3),
            ("Which element has the atomic number 1?", "Helium", "Hydrogen", "Lithium", "Oxygen", 2),
            ("What is the currency of Japan?", "Yuan", "Won", "Yen", "Dollar", 3),
            ("Who painted the Mona Lisa?", "Vincent van Gogh", "Leonardo da Vinci", "Pablo Picasso", "Claude Monet", 2),
            ("Which gas do plants absorb from the atmosphere?", "Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen", 3),
            ("What is the smallest prime number?", "0", "1", "2", "3", 3),
            ("Which country is famous for the Pyramids?", "Greece", "Egypt", "Italy", "Mexico", 2),
            ("What is the boiling point of water in Celsius?", "90°C", "100°C", "110°C", "120°C", 2),
            ("How many keys are on a standard piano?", "84", "86", "88", "90", 3),
            ("Which animal is known as the Ship of the Desert?", "Horse", "Elephant", "Camel", "Donkey", 3),
            ("Who was the first person to step on the Moon?", "Buzz Aldrin", "Neil Armstrong", "Yuri Gagarin", "Michael Collins", 2),
            ("What is the largest country in the world by land area?", "Canada", "China", "United States", "Russia", 4),
            ("How many bones are there in an adult human body?", "204", "206", "208", "210", 2),
            ("Which language is spoken in Brazil?", "Spanish", "Portuguese", "French", "English", 2),
            ("What is the primary capital city of Australia?", "Sydney", "Melbourne", "Brisbane", "Canberra", 4),
            ("Who discovered gravity?", "Albert Einstein", "Isaac Newton", "Galileo Galilei", "Nikola Tesla", 2),
            ("What is the hardest natural substance on Earth?", "Gold", "Iron", "Diamond", "Platinum", 3),
            ("Which country hosted the 2016 Summer Olympics?", "United Kingdom", "Russia", "China", "Brazil", 4),
            ("How many strings does a standard violin have?", "3", "4", "5", "6", 2),
            ("What is the chemical formula for water?", "HO", "H2O", "HO2", "H2O2", 2),
            ("Which is the largest organ of the human body?", "Liver", "Brain", "Skin", "Heart", 3),
            ("Who is the creator of the Python programming language?", "Dennis Ritchie", "Guido van Rossum", "James Gosling", "Bjarne Stroustrup", 2),
            ("What is the speed of light in a vacuum (approximate)?", "150,000 km/s", "300,000 km/s", "450,000 km/s", "600,000 km/s", 2),
            ("Which planet is closest to the Sun?", "Venus", "Mercury", "Earth", "Mars", 2),
            ("Who was the first President of the United States?", "Thomas Jefferson", "Abraham Lincoln", "George Washington", "John Adams", 3),
            ("What is the currency of the United Kingdom?", "Euro", "Pound Sterling", "Dollar", "Franc", 2),
            ("Which ocean is the smallest?", "Indian Ocean", "Pacific Ocean", "Southern Ocean", "Arctic Ocean", 4),
            ("How many degrees are in a right angle?", "45", "90", "180", "360", 2),
            ("Which bird is known for its ability to mimic human speech?", "Parrot", "Eagle", "Falcon", "Owl", 1),
            ("What is the national animal of India?", "Lion", "Elephant", "Leopard", "Bengal Tiger", 4),
            ("Who wrote the play 'Hamlet'?", "Charles Dickens", "Leo Tolstoy", "William Shakespeare", "Mark Twain", 3),
            ("Which country is known as the Land of the Rising Sun?", "China", "South Korea", "Japan", "Thailand", 3),
            ("What is the main ingredient in chocolate?", "Sugar", "Cocoa beans", "Milk", "Vanilla", 2),
            ("Which is the largest desert in the world?", "Sahara", "Gobi", "Arabian", "Antarctic Desert", 4),
            ("How many years are in a millennium?", "10", "100", "1000", "10000", 3),
            ("Who was the first woman to win a Nobel Prize?", "Marie Curie", "Jane Addams", "Mother Teresa", "Alva Myrdal", 1),
            ("Which mammal is capable of true flight?", "Flying Squirrel", "Bat", "Eagle", "Pigeon", 2),
            ("What is the chemical symbol for Sodium?", "S", "So", "Na", "N", 3),
            ("In what year did World War II end?", "1918", "1939", "1945", "1950", 3),
            ("What is the capital of Canada?", "Toronto", "Vancouver", "Ottawa", "Montreal", 3),
            ("How many colors are there in a rainbow?", "5", "6", "7", "8", 3),
            ("Who is the author of 'Harry Potter'?", "J.R.R. Tolkien", "George R.R. Martin", "J.K. Rowling", "Stephen King", 3),
            ("Which shape has five sides?", "Hexagon", "Pentagon", "Octagon", "Triangle", 2)
        ]

        questions_to_create = []
        for text, opt1, opt2, opt3, opt4, correct in questions_data:
            questions_to_create.append(
                Question(
                    quiz=quiz,
                    text=text,
                    option_1=opt1,
                    option_2=opt2,
                    option_3=opt3,
                    option_4=opt4,
                    correct_option=correct
                )
            )

        Question.objects.bulk_create(questions_to_create)
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(questions_to_create)} questions for Quiz ID {quiz.id}"))
