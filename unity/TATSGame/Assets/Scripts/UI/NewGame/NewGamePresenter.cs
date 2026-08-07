using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.NewGame
{
    /// <summary>
    /// NewGameScreen.uxml에 바인딩되는 presenter. docs/23_TITLE_SCREEN_BACKLOG.md T2 범위:
    /// 시작 교차로 3곳과 상대 AI(Luna·Terra·Sol) 중 하나씩 고르고 확정하는 입력만 다룬다.
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.2절과 같이 presenter는 상태 바인딩과 이벤트 연결만
    /// 하고 값을 계산하지 않는다 — 여기서 만드는 <see cref="NewGameSelection"/>은 사용자가 고른 그대로다.
    /// <c>POST /api/game-sessions</c> 호출과 <c>GameSessionSnapshot</c> 처리는 이 항목의 범위 밖이다:
    /// 저장소에 세션 API 구현이 없고(backend/README.md), GameSessionSnapshot 필드 계약도
    /// contracts/game-v2에 없다(계약 미정). 그래서 <see cref="Confirmed"/>는 선택값만 넘긴다.
    /// </summary>
    public sealed class NewGamePresenter : IDisposable
    {
        const string FocusedClass = "new-game__focusable--focused";
        const string SelectedClass = "new-game__option--selected";

        static readonly string[] IntersectionButtonNames =
        {
            "start-intersection-ix_04-button",
            "start-intersection-ix_09-button",
            "start-intersection-ix_07-button",
        };

        static readonly string[] OpponentButtonNames =
        {
            "opponent-luna-button",
            "opponent-terra-button",
            "opponent-sol-button",
        };

        readonly VisualElement _root;
        readonly Button[] _intersectionButtons;
        readonly Button[] _opponentButtons;
        readonly Button[] _focusOrder;
        readonly Button _backButton;
        readonly Button _startButton;

        int _focusedIndex;
        int _selectedIntersectionIndex = -1;
        int _selectedOpponentIndex = -1;
        bool _disposed;

        /// <summary>Esc 또는 `뒤로`. 이전 화면(시작 화면)으로 돌아가되 상태는 만들지 않는다.</summary>
        public event Action Back;

        /// <summary>둘 다 고른 뒤 `시작`. 실제 세션 생성 호출은 이 이벤트를 받는 쪽의 몫이며 T2 범위 밖이다.</summary>
        public event Action<NewGameSelection> Confirmed;

        public NewGamePresenter(VisualElement root)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));

            _intersectionButtons = ResolveButtons(IntersectionButtonNames);
            _opponentButtons = ResolveButtons(OpponentButtonNames);
            _backButton = ResolveButton("back-button");
            _startButton = ResolveButton("start-button");

            for (var i = 0; i < _intersectionButtons.Length; i++)
            {
                var capturedIndex = i;
                _intersectionButtons[i].clicked += () => SelectIntersection(capturedIndex);
            }

            for (var i = 0; i < _opponentButtons.Length; i++)
            {
                var capturedIndex = i;
                _opponentButtons[i].clicked += () => SelectOpponent(capturedIndex);
            }

            _backButton.clicked += RaiseBack;
            _startButton.clicked += TryConfirm;

            _focusOrder = BuildFocusOrder();

            UpdateStartButtonEnabled();
            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);
            SetFocusedIndex(0);
        }

        public void Dispose()
        {
            if (_disposed)
            {
                return;
            }

            _root.UnregisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);
            _disposed = true;
        }

        Button[] ResolveButtons(string[] names)
        {
            var buttons = new Button[names.Length];
            for (var i = 0; i < names.Length; i++)
            {
                buttons[i] = ResolveButton(names[i]);
            }

            return buttons;
        }

        Button ResolveButton(string name)
        {
            var button = _root.Q<Button>(name);
            if (button == null)
            {
                throw new InvalidOperationException(
                    $"NewGameScreen.uxml is missing the required button '{name}'.");
            }

            return button;
        }

        Button[] BuildFocusOrder()
        {
            var order = new List<Button>(_intersectionButtons.Length + _opponentButtons.Length + 2);
            order.AddRange(_intersectionButtons);
            order.AddRange(_opponentButtons);
            order.Add(_backButton);
            order.Add(_startButton);
            return order.ToArray();
        }

        void OnKeyDown(KeyDownEvent evt)
        {
            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                    SetFocusedIndex((_focusedIndex + 1) % _focusOrder.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.UpArrow:
                    SetFocusedIndex((_focusedIndex - 1 + _focusOrder.Length) % _focusOrder.Length);
                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    ActivateFocused();
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    // docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 12.1: Esc는 열린 화면을 한 단계 닫고
                    // 이전 선택을 보존한다. 여기서는 시작 화면으로 돌아가는 것 — 상태를 만들지 않는다.
                    RaiseBack();
                    evt.StopPropagation();
                    break;
            }
        }

        void SetFocusedIndex(int index)
        {
            _focusOrder[_focusedIndex].RemoveFromClassList(FocusedClass);
            _focusedIndex = index;
            _focusOrder[_focusedIndex].AddToClassList(FocusedClass);
            _focusOrder[_focusedIndex].Focus();
        }

        void ActivateFocused()
        {
            var focused = _focusOrder[_focusedIndex];

            var intersectionIndex = Array.IndexOf(_intersectionButtons, focused);
            if (intersectionIndex >= 0)
            {
                SelectIntersection(intersectionIndex);
                return;
            }

            var opponentIndex = Array.IndexOf(_opponentButtons, focused);
            if (opponentIndex >= 0)
            {
                SelectOpponent(opponentIndex);
                return;
            }

            if (focused == _backButton)
            {
                RaiseBack();
                return;
            }

            if (focused == _startButton)
            {
                TryConfirm();
            }
        }

        void SelectIntersection(int index)
        {
            if (_selectedIntersectionIndex >= 0)
            {
                _intersectionButtons[_selectedIntersectionIndex].RemoveFromClassList(SelectedClass);
            }

            _selectedIntersectionIndex = index;
            _intersectionButtons[index].AddToClassList(SelectedClass);
            UpdateStartButtonEnabled();
        }

        void SelectOpponent(int index)
        {
            if (_selectedOpponentIndex >= 0)
            {
                _opponentButtons[_selectedOpponentIndex].RemoveFromClassList(SelectedClass);
            }

            _selectedOpponentIndex = index;
            _opponentButtons[index].AddToClassList(SelectedClass);
            UpdateStartButtonEnabled();
        }

        void UpdateStartButtonEnabled()
        {
            _startButton.SetEnabled(_selectedIntersectionIndex >= 0 && _selectedOpponentIndex >= 0);
        }

        void RaiseBack()
        {
            Back?.Invoke();
        }

        void TryConfirm()
        {
            if (_selectedIntersectionIndex < 0 || _selectedOpponentIndex < 0)
            {
                return;
            }

            var startOption = NewGameContent.StartOptions[_selectedIntersectionIndex];
            var opponent = NewGameContent.Opponents[_selectedOpponentIndex];
            Confirmed?.Invoke(new NewGameSelection(startOption.IntersectionId, opponent));
        }
    }
}
