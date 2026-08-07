using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// ContinueScreen.uxml에 바인딩되는 presenter. docs/23_TITLE_SCREEN_BACKLOG.md T3 범위:
    /// 로컬 GameSave 슬롯 목록(버전·마지막 tick·도시 시각)을 보여주고, docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md
    /// 8.3절 <c>ConnectionState</c>의 <c>ResumeReady</c>(M15 재개 준비)·<c>ResumeFailed</c>(M16 재개 실패)
    /// 두 상태를 그린다.
    ///
    /// <c>POST /api/game-sessions/{id}/resume</c> 실제 호출은 이 항목의 범위 밖이다 — 저장소에 세션·resume
    /// API 구현이 없다(backend/README.md에는 content/map_eojin_playable.json과 테스트만 있다). 그래서
    /// <see cref="ResumeRequested"/>는 선택된 슬롯만 넘기고, 실제 검증 결과는 <see cref="ReportResumeSucceeded"/>·
    /// <see cref="ReportResumeFailed"/>를 밖에서 불러줘야 반영된다 — 아직 그걸 호출하는 코드는 없다.
    /// docs/22_TATS_BACKEND_DESIGN_V1.md 10절: 검증 실패는 "임의 병합 금지"이므로 재개 실패 화면은
    /// 이유·재시도·종료만 제공하고 그 밖의 조작은 막는다(M16).
    /// </summary>
    public sealed class ContinuePresenter : IDisposable
    {
        const string FocusedClass = "continue__focusable--focused";
        const string SelectedClass = "continue__option--selected";
        const string SlotButtonClass = "continue__option";

        enum Panel
        {
            SlotList,
            ResumeReady,
            ResumeFailed,
        }

        readonly VisualElement _root;
        readonly GameSaveSlotStore _slotStore;

        readonly VisualElement _slotListPanel;
        readonly VisualElement _slotsContainer;
        readonly Label _emptyLabel;
        readonly Button _backButton;
        readonly Button _resumeButton;

        readonly VisualElement _readyPanel;
        readonly Label _readySummaryLabel;
        readonly Button _readyBackButton;
        readonly Button _readyConfirmButton;

        readonly VisualElement _failedPanel;
        readonly Label _failedReasonLabel;
        readonly Button _failedQuitButton;
        readonly Button _failedRetryButton;

        readonly List<Button> _slotButtons = new List<Button>();
        List<GameSaveSlot> _slots = new List<GameSaveSlot>();

        Panel _activePanel = Panel.SlotList;
        Button[] _focusOrder = Array.Empty<Button>();
        int _focusedIndex;
        int _selectedSlotIndex = -1;
        GameSaveSlot? _pendingSlot;
        bool _disposed;

        /// <summary>Esc(슬롯 목록 화면). 이전 화면(시작 화면)으로 돌아가되 상태는 만들지 않는다.</summary>
        public event Action Back;

        /// <summary>슬롯을 고르고 `이어하기`(또는 재개 실패에서 `재시도`)를 누르면 발행한다.
        /// 실제 <c>POST /resume</c> 호출은 이 이벤트를 받는 쪽의 몫이며 T3 범위 밖이다.</summary>
        public event Action<GameSaveSlot> ResumeRequested;

        /// <summary>재개 준비 화면에서 `재개`를 누르면 발행한다. 실제 게임 진입은 범위 밖이다.</summary>
        public event Action<GameSaveSlot> Resumed;

        /// <summary>재개 실패 화면에서 `종료`를 누르면 발행한다.</summary>
        public event Action Quit;

        public ContinuePresenter(VisualElement root, GameSaveSlotStore slotStore)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _slotStore = slotStore ?? throw new ArgumentNullException(nameof(slotStore));

            _slotListPanel = Resolve<VisualElement>("continue-slot-list");
            _slotsContainer = Resolve<VisualElement>("continue-slots");
            _emptyLabel = Resolve<Label>("continue-empty-label");
            _backButton = Resolve<Button>("continue-back-button");
            _resumeButton = Resolve<Button>("continue-resume-button");

            _readyPanel = Resolve<VisualElement>("continue-resume-ready");
            _readySummaryLabel = Resolve<Label>("continue-ready-summary");
            _readyBackButton = Resolve<Button>("continue-ready-back-button");
            _readyConfirmButton = Resolve<Button>("continue-ready-confirm-button");

            _failedPanel = Resolve<VisualElement>("continue-resume-failed");
            _failedReasonLabel = Resolve<Label>("continue-failed-reason");
            _failedQuitButton = Resolve<Button>("continue-failed-quit-button");
            _failedRetryButton = Resolve<Button>("continue-failed-retry-button");

            _backButton.clicked += RaiseBack;
            _resumeButton.clicked += TryRequestResume;
            _readyBackButton.clicked += ReturnToSlotList;
            _readyConfirmButton.clicked += ConfirmResume;
            _failedQuitButton.clicked += RaiseQuit;
            _failedRetryButton.clicked += RetryResume;

            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);

            ReloadSlots();
            ShowPanel(Panel.SlotList);
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

        /// <summary>슬롯 목록을 다시 읽는다. 화면을 열 때 한 번 호출한다.</summary>
        public void ReloadSlots()
        {
            foreach (var button in _slotButtons)
            {
                _slotsContainer.Remove(button);
            }

            _slotButtons.Clear();

            var result = _slotStore.LoadSlots();
            _slots = new List<GameSaveSlot>(result.Slots);

            foreach (var slot in _slots)
            {
                var button = new Button { text = BuildSlotLabel(slot), name = $"continue-slot-{slot.SlotId}-button" };
                button.AddToClassList(SlotButtonClass);
                var capturedIndex = _slotButtons.Count;
                button.clicked += () => SelectSlot(capturedIndex);
                _slotsContainer.Add(button);
                _slotButtons.Add(button);
            }

            _selectedSlotIndex = -1;
            UpdateResumeButtonEnabled();

            var hasSlots = _slots.Count > 0;
            _slotsContainer.style.display = hasSlots ? DisplayStyle.Flex : DisplayStyle.None;
            _emptyLabel.style.display = hasSlots ? DisplayStyle.None : DisplayStyle.Flex;
            _emptyLabel.text = !hasSlots && result.State == GameSaveSlotListState.Error
                ? "저장 파일을 읽을 수 없습니다. 파일이 손상되었을 수 있습니다."
                : "저장된 게임이 없습니다.";

            if (_activePanel == Panel.SlotList)
            {
                RebuildSlotListFocusOrder();
            }
        }

        void RebuildSlotListFocusOrder()
        {
            var order = new List<Button>(_slotButtons.Count + 2);
            order.AddRange(_slotButtons);
            order.Add(_backButton);
            order.Add(_resumeButton);
            _focusOrder = order.ToArray();
            SetFocusedIndex(0);
        }

        void ShowPanel(Panel panel)
        {
            _activePanel = panel;
            _slotListPanel.style.display = panel == Panel.SlotList ? DisplayStyle.Flex : DisplayStyle.None;
            _readyPanel.style.display = panel == Panel.ResumeReady ? DisplayStyle.Flex : DisplayStyle.None;
            _failedPanel.style.display = panel == Panel.ResumeFailed ? DisplayStyle.Flex : DisplayStyle.None;

            switch (panel)
            {
                case Panel.SlotList:
                    RebuildSlotListFocusOrder();
                    break;

                case Panel.ResumeReady:
                    _focusOrder = new[] { _readyBackButton, _readyConfirmButton };
                    SetFocusedIndex(1); // 기본 포커스는 `재개`
                    break;

                case Panel.ResumeFailed:
                    // docs/20 M16: 재개 실패는 이유·재시도·종료만 제공한다.
                    _focusOrder = new[] { _failedQuitButton, _failedRetryButton };
                    SetFocusedIndex(1); // 기본 포커스는 `재시도`
                    break;
            }
        }

        void OnKeyDown(KeyDownEvent evt)
        {
            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                    if (_focusOrder.Length > 0)
                    {
                        SetFocusedIndex((_focusedIndex + 1) % _focusOrder.Length);
                    }

                    evt.StopPropagation();
                    break;

                case KeyCode.UpArrow:
                    if (_focusOrder.Length > 0)
                    {
                        SetFocusedIndex((_focusedIndex - 1 + _focusOrder.Length) % _focusOrder.Length);
                    }

                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    ActivateFocused();
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    OnEscape();
                    evt.StopPropagation();
                    break;
            }
        }

        void OnEscape()
        {
            switch (_activePanel)
            {
                case Panel.SlotList:
                    // docs/20 12.1: Esc는 열린 화면을 한 단계 닫는다 — 여기서는 시작 화면으로.
                    RaiseBack();
                    break;

                case Panel.ResumeReady:
                    // 재개를 확정하기 전이면 슬롯 목록으로 되돌아가는 것도 취소와 같은 뜻이다.
                    ReturnToSlotList();
                    break;

                case Panel.ResumeFailed:
                    // M16: 재개 실패는 이유·재시도·종료만 제공한다. Esc를 둘 중 하나로 임의 연결하지
                    // 않고 입력만 흡수한다(T1의 Esc-흡수와 같은 방식) — 실수로 종료되는 것을 막는다.
                    break;
            }
        }

        void SetFocusedIndex(int index)
        {
            if (_focusOrder.Length == 0)
            {
                return;
            }

            foreach (var button in _focusOrder)
            {
                button.RemoveFromClassList(FocusedClass);
            }

            _focusedIndex = Mathf.Clamp(index, 0, _focusOrder.Length - 1);
            var focused = _focusOrder[_focusedIndex];
            focused.AddToClassList(FocusedClass);
            focused.Focus();
        }

        void ActivateFocused()
        {
            if (_focusOrder.Length == 0)
            {
                return;
            }

            var focused = _focusOrder[_focusedIndex];

            var slotIndex = _slotButtons.IndexOf(focused);
            if (slotIndex >= 0)
            {
                SelectSlot(slotIndex);
                return;
            }

            if (focused == _backButton)
            {
                RaiseBack();
            }
            else if (focused == _resumeButton)
            {
                TryRequestResume();
            }
            else if (focused == _readyBackButton)
            {
                ReturnToSlotList();
            }
            else if (focused == _readyConfirmButton)
            {
                ConfirmResume();
            }
            else if (focused == _failedQuitButton)
            {
                RaiseQuit();
            }
            else if (focused == _failedRetryButton)
            {
                RetryResume();
            }
        }

        void SelectSlot(int index)
        {
            if (_selectedSlotIndex >= 0 && _selectedSlotIndex < _slotButtons.Count)
            {
                _slotButtons[_selectedSlotIndex].RemoveFromClassList(SelectedClass);
            }

            _selectedSlotIndex = index;
            _slotButtons[index].AddToClassList(SelectedClass);
            UpdateResumeButtonEnabled();
        }

        void UpdateResumeButtonEnabled()
        {
            _resumeButton.SetEnabled(_selectedSlotIndex >= 0 && _selectedSlotIndex < _slots.Count);
        }

        void RaiseBack()
        {
            Back?.Invoke();
        }

        void TryRequestResume()
        {
            if (_selectedSlotIndex < 0 || _selectedSlotIndex >= _slots.Count)
            {
                return;
            }

            var slot = _slots[_selectedSlotIndex];
            _pendingSlot = slot;
            ResumeRequested?.Invoke(slot);
        }

        void RetryResume()
        {
            if (_pendingSlot == null)
            {
                return;
            }

            ResumeRequested?.Invoke(_pendingSlot.Value);
        }

        void ReturnToSlotList()
        {
            ShowPanel(Panel.SlotList);
        }

        void ConfirmResume()
        {
            if (_pendingSlot == null)
            {
                return;
            }

            Resumed?.Invoke(_pendingSlot.Value);
        }

        void RaiseQuit()
        {
            Quit?.Invoke();
        }

        /// <summary>
        /// 실제 <c>POST /resume</c> 응답을 받은 쪽(T3 범위 밖)이 성공 검증 결과로 호출한다.
        /// M15 재개 준비 화면을 보여준다.
        /// </summary>
        public void ReportResumeSucceeded()
        {
            if (_pendingSlot == null)
            {
                return;
            }

            _readySummaryLabel.text = BuildSlotLabel(_pendingSlot.Value);
            ShowPanel(Panel.ResumeReady);
        }

        /// <summary>
        /// 실제 <c>POST /resume</c> 응답을 받은 쪽(T3 범위 밖)이 실패 사유와 함께 호출한다.
        /// M16 재개 실패 화면을 보여준다 — 임의 병합 없이 이유·재시도·종료만 제공한다.
        /// </summary>
        public void ReportResumeFailed(string reason)
        {
            _failedReasonLabel.text = reason;
            ShowPanel(Panel.ResumeFailed);
        }

        static string BuildSlotLabel(GameSaveSlot slot)
        {
            // docs/22_TATS_BACKEND_DESIGN_V1.md 2절: 도시 시각 = day = tick // 86400, timeOfDay = tick % 86400.
            // docs/19_TATS_UI_UX_DIRECTION_V1.md 64행: "Day N · HH:MM" 문구 고정.
            var day = slot.LastConfirmedTick / 86400;
            var secondsOfDay = slot.LastConfirmedTick % 86400;
            var hour = secondsOfDay / 3600;
            var minute = secondsOfDay % 3600 / 60;
            return $"{slot.StartNodeId} · {slot.OpponentModel} · v{slot.SchemaVersion} · "
                + $"tick {slot.LastConfirmedTick} · Day {day} · {hour:D2}:{minute:D2}";
        }

        T Resolve<T>(string name) where T : VisualElement
        {
            var element = _root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException($"ContinueScreen.uxml is missing the required element '{name}'.");
            }

            return element;
        }
    }
}
