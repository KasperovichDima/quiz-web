from account.models import CustomUser

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django.views.generic.list import MultipleObjectMixin

from quiz.forms import ChoicesFormSet
from quiz.models import Exam, Question, Result


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/list.html'
    context_object_name = 'exams'


class ExamDetailView(LoginRequiredMixin, DetailView, MultipleObjectMixin):
    model = Exam
    template_name = 'exams/details.html'
    context_object_name = 'exam'
    pk_url_kwarg = 'uuid'
    paginate_by = 5

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return self.model.objects.get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(object_list=self.get_queryset(), **kwargs)
        return context

    def get_queryset(self):
        return Result.objects.filter(
            exam=self.get_object(),
            user=self.request.user
        ).order_by('state')


class ExamResultCreateView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        result = Result.objects.create(
            user=request.user,
            exam=Exam.objects.get(uuid=uuid),
            state=Result.STATE.IN_PROGRESS
        )

        result.save()

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,
                    # 'order_num': 1
                }
            )
        )


class ExamResultQuestionView(LoginRequiredMixin, UpdateView):
    def __get_res_by_uuid(self, **kwargs):
        return Result.objects.get(uuid=kwargs.get('res_uuid'))

    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        question = Question.objects.get(
            exam__uuid=uuid,
            # далее мы в методе получаем результат, а у него получаем current_order_number
            order_num=self.__get_res_by_uuid(**kwargs).current_order_number + 1
        )

        choices = ChoicesFormSet(queryset=question.choices.all())

        return render(request, 'exams/question.html',
                      context={'question': question, 'choices': choices})

    def post(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        result = self.__get_res_by_uuid(**kwargs)
        question = Question.objects.get(
            exam__uuid=uuid,
            order_num=result.current_order_number + 1
        )
        choices = ChoicesFormSet(data=request.POST)
        selected_choices = ['is_selected' in form.changed_data for form in choices.forms]

        # обрабатываем ситуацию, когда пользователь отметил все ответы, или ни одного
        if not (0 < sum(selected_choices) < len(choices)):
            messages.warning(request, 'Нельзя выбирать все ответы одновременно или ни одного')
            choices = ChoicesFormSet(queryset=question.choices.all())
            return render(request, 'exams/question.html',
                          context={'question': question, 'choices': choices})

        result.update_result(result.current_order_number + 1, question, selected_choices)

        if result.state == Result.STATE.FINISHED:
            return HttpResponseRedirect(
                reverse(
                    'quizzes:result_details',
                    kwargs={
                        'uuid': uuid,
                        'res_uuid': result.uuid
                    }
                )
            )

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': res_uuid,
                    # 'order_num': order_num + 1
                }
            )
        )


class ExamResultDetailView(LoginRequiredMixin, DetailView):
    model = Result
    template_name = 'results/details.html'
    context_object_name = 'result'
    pk_url_kwarg = 'uuid'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('res_uuid')
        return self.get_queryset().get(uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = self.get_object().exam
        correct_perc: int = exam.get_correct_perc_by_user(self.request.user)
        context['correct_perc'] = correct_perc
        return context


class RatingView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'results/rating.html'
    context_object_name = 'users'
    queryset = model.objects.all().order_by('-rating')


class ExamResultUpdateView(LoginRequiredMixin, UpdateView):
    def get(self, request, *args, **kwargs):
        uuid = kwargs.get('uuid')
        res_uuid = kwargs.get('res_uuid')
        user = request.user

        result = Result.objects.get(
            user=user,
            uuid=res_uuid,
            exam__uuid=uuid
        )

        return HttpResponseRedirect(
            reverse(
                'quizzes:question',
                kwargs={
                    'uuid': uuid,
                    'res_uuid': result.uuid,
                    # 'order_num': result.current_order_number + 1
                }
            )
        )


class ExamResultDeleteView(DeleteView):
    template_name ='results/delete.html'
    model = Result
    context_object_name = 'result'

    def get_object(self, queryset=None):
        return Result.objects.get(uuid=self.kwargs['res_uuid'])

    def get_success_url(self):
        return reverse_lazy('quizzes:details', kwargs={'uuid': self.kwargs['uuid']})

