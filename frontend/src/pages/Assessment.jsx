import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Assessment() {
  const navigate = useNavigate();
  const timeoutHandled = useRef(false);

  const [attempt, setAttempt] = useState(null);
  const [aptitudeQuestions, setAptitudeQuestions] = useState([]);
  const [riasecQuestions, setRiasecQuestions] = useState([]);
  const [aptitudeAnswers, setAptitudeAnswers] = useState({});
  const [riasecAnswers, setRiasecAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [pauseLoading, setPauseLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    const loadAssessment = async () => {
      try {
        setError("");

        const startResponse = await api.post("/aptitude/start");
        const questionsResponse = await api.get("/aptitude/questions");

        setAttempt(startResponse.data);
        setRemainingSeconds(startResponse.data.remaining_seconds || 0);
        setIsPaused(startResponse.data.status === "paused");

        if (
          startResponse.data.status === "in_progress" ||
          startResponse.data.status === "paused"
        ) {
          localStorage.setItem("assessment_locked", "true");

          window.dispatchEvent(
            new Event("assessment-lock-changed")
          );
        }

        setAptitudeQuestions(
          questionsResponse.data.aptitude_questions || []
        );

        setRiasecQuestions(
          questionsResponse.data.riasec_questions || []
        );
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load the assessment."
        );
      } finally {
        setLoading(false);
      }
    };

    loadAssessment();
  }, []);

  /*
   * Handle assessment timeout.
   *
   * When the frontend timer reaches 00:00,
   * the backend is asked to reset the attempt.
   */
  const handleTimeout = async () => {
    if (!attempt?.attempt_id || timeoutHandled.current) {
      return;
    }

    timeoutHandled.current = true;
    setError("");

    try {
      await api.post(
        `/aptitude/${attempt.attempt_id}/timeout`
      );

      // Remove the assessment lock
      localStorage.removeItem("assessment_locked");

      window.dispatchEvent(
        new Event("assessment-lock-changed")
      );

      // Clear local assessment state
      setAttempt(null);
      setAptitudeAnswers({});
      setRiasecAnswers({});
      setResult(null);
      setRemainingSeconds(0);
      setIsPaused(false);

      // Return student to home
      navigate("/student/home", { replace: true });
    } catch (err) {
      timeoutHandled.current = false;

      setError(
        err.response?.data?.detail ||
          "The assessment timed out, but could not be reset."
      );
    }
  };

  /*
   * Assessment countdown timer.
   */
  useEffect(() => {
    if (isPaused || remainingSeconds <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setRemainingSeconds((previous) => {
        if (previous <= 1) {
          clearInterval(timer);
          return 0;
        }

        return previous - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [remainingSeconds, isPaused]);

  /*
   * Detect when the countdown reaches 00:00.
   */
  useEffect(() => {
    if (
      remainingSeconds === 0 &&
      attempt?.status === "in_progress" &&
      !isPaused
    ) {
      handleTimeout();
    }
  }, [remainingSeconds, attempt, isPaused]);

  const handleAptitudeAnswer = (questionId, optionIndex) => {
    if (isPaused) {
      return;
    }

    setAptitudeAnswers((previous) => ({
      ...previous,
      [questionId]: optionIndex,
    }));
  };

  const handleRiasecAnswer = (questionId, value) => {
    if (isPaused) {
      return;
    }

    setRiasecAnswers((previous) => ({
      ...previous,
      [questionId]: value,
    }));
  };

  const handlePause = async () => {
    if (!attempt?.attempt_id || pauseLoading) {
      return;
    }

    setPauseLoading(true);

    try {
      if (!isPaused) {
        const response = await api.post(
          `/aptitude/${attempt.attempt_id}/pause`
        );

        setRemainingSeconds(response.data.remaining_seconds);
        setIsPaused(true);

        setAttempt((previous) => ({
          ...previous,
          status: "paused",
        }));

        localStorage.setItem(
          "assessment_locked",
          "true"
        );

        window.dispatchEvent(
          new Event("assessment-lock-changed")
        );
      } else {
        const response = await api.post(
          `/aptitude/${attempt.attempt_id}/resume`
        );

        setRemainingSeconds(response.data.remaining_seconds);
        setIsPaused(false);

        setAttempt((previous) => ({
          ...previous,
          status: "in_progress",
        }));

        localStorage.setItem(
          "assessment_locked",
          "true"
        );

        window.dispatchEvent(
          new Event("assessment-lock-changed")
        );
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to update the assessment."
      );
    } finally {
      setPauseLoading(false);
    }
  };

  const allQuestionsAnswered =
    aptitudeQuestions.every(
      (question) =>
        aptitudeAnswers[question.id] !== undefined
    ) &&
    riasecQuestions.every(
      (question) =>
        riasecAnswers[question.id] !== undefined
    );

  const handleSubmit = async () => {
    if (!attempt?.attempt_id || submitLoading) {
      return;
    }

    setError("");

    if (!allQuestionsAnswered) {
      setError(
        "Please answer every question before submitting the assessment."
      );
      return;
    }

    setSubmitLoading(true);

    try {
      const response = await api.post(
        `/aptitude/${attempt.attempt_id}/submit`,
        {
          aptitude_answers: aptitudeAnswers,
          riasec_answers: riasecAnswers,
        }
      );

      setResult(response.data.result);
      setRemainingSeconds(0);
      setIsPaused(true);

      setAttempt((previous) => ({
        ...previous,
        status: "completed",
      }));

      localStorage.removeItem(
        "assessment_locked"
      );

      window.dispatchEvent(
        new Event("assessment-lock-changed")
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to submit the assessment."
      );
    } finally {
      setSubmitLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(
      (seconds % 3600) / 60
    );
    const secs = seconds % 60;

    return `${String(hours).padStart(2, "0")}:${String(
      minutes
    ).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">
          Preparing your assessment...
        </h1>

        <p className="mt-2 text-slate-500">
          Loading your questions.
        </p>
      </div>
    );
  }

  if (error && !attempt) {
    return (
      <div className="rounded-3xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-red-600">
          Assessment Error
        </h1>

        <p className="mt-2 text-slate-600">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
          Your Assessment
        </p>

        <h1 className="mt-2 text-4xl font-bold text-slate-900">
          Discover Your Strengths
        </h1>

        <p className="mt-3 max-w-2xl text-slate-500">
          Answer each question based on your own abilities,
          interests, and preferences.
        </p>
      </div>

      {attempt && (
        <div className="mb-8 rounded-3xl bg-violet-600 p-6 text-white shadow-sm">
          <p className="text-sm font-semibold text-violet-200">
            ASSESSMENT STATUS
          </p>

          <h2 className="mt-2 text-2xl font-bold">
            {attempt.status === "in_progress"
              ? "Assessment in progress"
              : attempt.status === "paused"
              ? "Assessment paused"
              : "Assessment complete"}
          </h2>

          <div className="mt-4">
            <p className="text-sm text-violet-200">
              Time Remaining
            </p>

            <p className="mt-1 text-3xl font-bold tracking-wider">
              {formatTime(remainingSeconds)}
            </p>
          </div>

          {attempt.status === "in_progress" && (
            <button
              type="button"
              onClick={handlePause}
              disabled={pauseLoading}
              className="mt-5 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pauseLoading
                ? "Please wait..."
                : "Pause Assessment"}
            </button>
          )}

          {attempt.status === "paused" && (
            <button
              type="button"
              onClick={handlePause}
              disabled={pauseLoading}
              className="mt-5 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pauseLoading
                ? "Please wait..."
                : "Resume Assessment"}
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="mb-8 rounded-2xl bg-red-50 px-5 py-4 text-sm font-medium text-red-600">
          {error}
        </div>
      )}

      {aptitudeQuestions.length > 0 && !result && (
        <section className="mb-10">
          <div className="mb-6">
            <p className="text-sm font-semibold text-violet-600">
              PART 01
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-900">
              Aptitude Assessment
            </h2>

            <p className="mt-2 text-slate-500">
              Test your reasoning and problem-solving abilities.
            </p>
          </div>

          <div className="space-y-6">
            {aptitudeQuestions.map((question, index) => (
              <div
                key={question.id}
                className="rounded-3xl bg-white p-6 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <p className="text-sm font-semibold text-violet-600">
                    Question {index + 1}
                  </p>

                  {question.difficulty && (
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      Difficulty {question.difficulty}
                    </span>
                  )}
                </div>

                <h3 className="mt-4 text-lg font-semibold leading-7 text-slate-900">
                  {question.prompt}
                </h3>

                <div className="mt-5 space-y-3">
                  {question.options.map(
                    (option, optionIndex) => {
                      const selected =
                        aptitudeAnswers[question.id] ===
                        optionIndex;

                      return (
                        <button
                          key={optionIndex}
                          type="button"
                          disabled={isPaused}
                          onClick={() =>
                            handleAptitudeAnswer(
                              question.id,
                              optionIndex
                            )
                          }
                          className={`w-full rounded-2xl border px-4 py-4 text-left text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${
                            selected
                              ? "border-violet-600 bg-violet-50 text-violet-700"
                              : "border-slate-200 bg-white text-slate-700 hover:border-violet-300 hover:bg-slate-50"
                          }`}
                        >
                          {option}
                        </button>
                      );
                    }
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {riasecQuestions.length > 0 && !result && (
        <section className="mb-10">
          <div className="mb-6">
            <p className="text-sm font-semibold text-violet-600">
              PART 02
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-900">
              Interest Assessment
            </h2>

            <p className="mt-2 text-slate-500">
              Choose how much each statement describes you.
            </p>
          </div>

          <div className="space-y-6">
            {riasecQuestions.map((question, index) => (
              <div
                key={question.id}
                className="rounded-3xl bg-white p-6 shadow-sm"
              >
                <p className="text-sm font-semibold text-violet-600">
                  Question {index + 1}
                </p>

                <h3 className="mt-4 text-lg font-semibold leading-7 text-slate-900">
                  {question.statement}
                </h3>

                <div className="mt-5 grid grid-cols-5 gap-2">
                  {[1, 2, 3, 4, 5].map((value) => {
                    const selected =
                      riasecAnswers[question.id] === value;

                    return (
                      <button
                        key={value}
                        type="button"
                        disabled={isPaused}
                        onClick={() =>
                          handleRiasecAnswer(
                            question.id,
                            value
                          )
                        }
                        className={`rounded-2xl border px-3 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                          selected
                            ? "border-violet-600 bg-violet-600 text-white"
                            : "border-slate-200 bg-white text-slate-700 hover:border-violet-300"
                        }`}
                      >
                        {value}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {result && (
        <div className="mb-8 rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-violet-600">
            Assessment Complete
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Your Career Result
          </h2>

          <div className="mt-6 rounded-2xl bg-violet-50 p-6">
            <p className="text-sm font-semibold text-violet-600">
              TOP CAREER FIELD
            </p>

            <h3 className="mt-2 text-2xl font-bold text-slate-900">
              {result.career_field}
            </h3>

            <p className="mt-3 text-lg font-semibold text-violet-700">
              {result.score}% Match
            </p>
          </div>

          <div className="mt-6">
            <p className="text-sm font-semibold text-violet-600">
              YOUR PERSONA
            </p>

            <h3 className="mt-2 text-xl font-bold text-slate-900">
              {result.persona?.name}
            </h3>

            <p className="mt-2 text-slate-500">
              {result.persona?.description}
            </p>
          </div>

          <div className="mt-6">
            <p className="text-sm font-semibold text-violet-600">
              YOUR SUMMARY
            </p>

            <p className="mt-2 leading-7 text-slate-600">
              {result.summary}
            </p>
          </div>

          {result.recommendations?.length > 0 && (
            <div className="mt-8">
              <p className="text-sm font-semibold text-violet-600">
                RECOMMENDED CAREER PATHS
              </p>

              <div className="mt-4 space-y-4">
                {result.recommendations.map(
                  (recommendation, index) => (
                    <div
                      key={index}
                      className="rounded-2xl border border-slate-200 p-5"
                    >
                      <h3 className="text-lg font-bold text-slate-900">
                        {recommendation.name ||
                          recommendation.career_field ||
                          recommendation.title ||
                          `Career Path ${index + 1}`}
                      </h3>

                      {recommendation.description && (
                        <p className="mt-2 text-sm leading-6 text-slate-500">
                          {recommendation.description}
                        </p>
                      )}
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {result.trait_scores && (
            <div className="mt-8">
              <p className="text-sm font-semibold text-violet-600">
                YOUR TRAIT SCORES
              </p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {Object.entries(
                  result.trait_scores
                ).map(([trait, score]) => (
                  <div
                    key={trait}
                    className="rounded-2xl bg-slate-50 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium capitalize text-slate-700">
                        {trait.replaceAll("_", " ")}
                      </p>

                      <p className="text-sm font-bold text-violet-600">
                        {score}%
                      </p>
                    </div>

                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                      <div
                        className="h-full rounded-full bg-violet-600"
                        style={{
                          width: `${Math.min(
                            Math.max(score, 0),
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!result && (
        <div className="rounded-3xl bg-slate-900 p-8 text-white">
          <h2 className="text-2xl font-bold">
            Assessment Loaded
          </h2>

          <p className="mt-2 text-sm text-slate-300">
            {aptitudeQuestions.length} aptitude questions
            and {riasecQuestions.length} interest questions
            loaded.
          </p>

          <p className="mt-4 text-sm text-slate-400">
            {allQuestionsAnswered
              ? "All questions answered. You can submit your assessment."
              : "Answer every question to unlock the submit button."}
          </p>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={
              submitLoading ||
              isPaused ||
              !allQuestionsAnswered ||
              attempt?.status === "completed" ||
              remainingSeconds <= 0
            }
            className="mt-6 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitLoading
              ? "Processing Results..."
              : "Submit Assessment"}
          </button>
        </div>
      )}
    </div>
  );
}

export default Assessment;