from core.models import BaseModel
from core.utils import generate_uuid

from django.contrib.auth import get_user_model
from django.db import models


class Exam(BaseModel):
    QUESTION_MIN_LIMIT = 3
    QUESTION_MAX_LIMIT = 20
    QUESTION_FIRST_NUMBER = 1
    QUESTION_NUM_STEP = 1

    class LEVEL(models.IntegerChoices):
        BASIC = 0, 'Basic'
        MIDDLE = 1, 'Middle'
        ADVANCED = 2, 'Advanced'

    uuid = models.UUIDField(default=generate_uuid, db_index=True, unique=True)
    title = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    level = models.PositiveSmallIntegerField(choices=LEVEL.choices, default=LEVEL.BASIC)

    class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return self.title

    def question_count(self):
        return self.questions.count()

    def get_correct_perc_by_user(self, user):
        '''
        Вычисляет процент правильных ответов пользователя
        за все попытки по данному тесту
        :param user: Текущий пользователь
        :return: процент правильных ответов (int)
        '''
        exam_results = Result.objects.filter(user=user, exam=self)
        correct_num = total_num = 0
        for res in exam_results:
            correct_num += res.num_correct_answers
            total_num += res.num_incorrect_answers+res.num_correct_answers
        return correct_num * 100 // total_num


class Question(BaseModel):
    exam = models.ForeignKey(Exam, related_name='questions', on_delete=models.CASCADE)
    order_num = models.PositiveSmallIntegerField()
    text = models.CharField(max_length=2048)
    image = models.ImageField(null=True, blank=True, upload_to='questions/')

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'


class Result(BaseModel):
    class STATE(models.IntegerChoices):
        IN_PROGRESS = 0, "In progress"
        FINISHED = 1, "Finished"

    user = models.ForeignKey(get_user_model(), related_name='results', on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, related_name='results', on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField(default=STATE.IN_PROGRESS, choices=STATE.choices)
    uuid = models.UUIDField(default=generate_uuid, db_index=True, unique=True)
    current_order_number = models.PositiveSmallIntegerField(default=0)
    num_correct_answers = models.PositiveSmallIntegerField(default=0)
    num_incorrect_answers = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    def update_result(self, order_number, question, selected_choices):
        correct_choice = [choice.is_correct for choice in question.choices.all()]
        correct_answer = True
        for z in zip(selected_choices, correct_choice):
            correct_answer &= (z[0] == z[1])

        self.num_correct_answers += int(correct_answer)
        self.num_incorrect_answers += 1 - int(correct_answer)
        self.current_order_number = order_number

        if order_number == question.exam.question_count():
            self.state = self.STATE.FINISHED
            self.user.update_rating(self.test_points())
        self.save()

    def success_rate(self):
        return int(self.num_correct_answers / self.exam.question_count() * 100)

    def test_time(self):
        return self.update_timestamp - self.create_timestamp

    def test_points(self):
        return max(0, self.num_correct_answers - self.num_incorrect_answers)

    # def result_by_user_and_exam(self, user, exam):
    #     results = self.objects.fetch(user=user, exam=exam)

