using System;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Help
{
    /// <summary>
    /// HelpScreen.uxml에 바인딩되는 presenter. docs/23_TITLE_SCREEN_BACKLOG.md T5 범위: 첫 3분 안내·
    /// 조작법·용어(대기행렬·spillback·상충·포화도) 세 탭을 <see cref="HelpContentStore"/>가 읽은
    /// <c>help.json</c> 내용으로 그린다. 본문 문자열은 여기 코드에 없다 — 전부 콘텐츠에서 온다.
    ///
    /// 상하 화살표로 탭 3개와 `뒤로` 사이에서 포커스를 이동하고, Enter로 탭을 전환하거나 `뒤로`를
    /// 활성화한다. 좌우 화살표·Enter로 값을 바꾸는 T4 환경설정 화면과 달리 이 화면은 읽기 전용
    /// 정보만 보여주므로 탭 전환에 Enter를 그대로 재사용했다 — 문서에 정해진 규칙은 아니고
    /// 이번 구현의 결정이다. Esc는 T1~T4와 같은 방식으로 `뒤로`와 같은 동작을 한다.
    /// </summary>
    public sealed class HelpPresenter : IDisposable
    {
        const string FocusedClass = "help__focusable--focused";
        const string ActiveTabClass = "help__tab--active";

        readonly VisualElement _root;
        readonly HelpContentStore _store;

        readonly Button _firstThreeMinutesTabButton;
        readonly Button _controlsTabButton;
        readonly Button _termsTabButton;
        readonly Button _backButton;
        readonly VisualElement _contentContainer;
        readonly Label _errorLabel;

        readonly Button[] _focusOrder;
        int _focusedIndex;
        HelpContentDto _content;
        HelpSection _activeSection = HelpSection.FirstThreeMinutes;
        bool _disposed;

        /// <summary>`뒤로` 또는 Esc.</summary>
        public event Action Back;

        public HelpPresenter(VisualElement root, HelpContentStore store)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _store = store ?? throw new ArgumentNullException(nameof(store));

            _firstThreeMinutesTabButton = Resolve<Button>("help-tab-first3min-button");
            _controlsTabButton = Resolve<Button>("help-tab-controls-button");
            _termsTabButton = Resolve<Button>("help-tab-terms-button");
            _backButton = Resolve<Button>("help-back-button");
            _contentContainer = Resolve<VisualElement>("help-content");
            _errorLabel = Resolve<Label>("help-error-label");

            _focusOrder = new[] { _firstThreeMinutesTabButton, _controlsTabButton, _termsTabButton, _backButton };

            _firstThreeMinutesTabButton.clicked += () => ActivateFocusIndex(0);
            _controlsTabButton.clicked += () => ActivateFocusIndex(1);
            _termsTabButton.clicked += () => ActivateFocusIndex(2);
            _backButton.clicked += RaiseBack;

            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);

            ReloadContent();
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

        /// <summary>help.json을 다시 읽고 현재 탭을 다시 그린다.</summary>
        public void ReloadContent()
        {
            var result = _store.Load();
            if (result.State == HelpContentLoadState.Error)
            {
                _content = null;
                _errorLabel.text = $"도움말을 불러오지 못했습니다: {result.FailureReason}";
                _errorLabel.style.display = DisplayStyle.Flex;
                _contentContainer.Clear();
                return;
            }

            _content = result.Content;
            _errorLabel.style.display = DisplayStyle.None;
            ShowSection(_activeSection);
        }

        void ShowSection(HelpSection section)
        {
            _activeSection = section;

            _firstThreeMinutesTabButton.RemoveFromClassList(ActiveTabClass);
            _controlsTabButton.RemoveFromClassList(ActiveTabClass);
            _termsTabButton.RemoveFromClassList(ActiveTabClass);

            _contentContainer.Clear();

            if (_content == null)
            {
                return;
            }

            switch (section)
            {
                case HelpSection.FirstThreeMinutes:
                    _firstThreeMinutesTabButton.AddToClassList(ActiveTabClass);
                    RenderFirstThreeMinutes();
                    break;

                case HelpSection.Controls:
                    _controlsTabButton.AddToClassList(ActiveTabClass);
                    RenderControls();
                    break;

                case HelpSection.Terms:
                    _termsTabButton.AddToClassList(ActiveTabClass);
                    RenderTerms();
                    break;
            }
        }

        void RenderFirstThreeMinutes()
        {
            var section = _content.FirstThreeMinutes;
            AddRow(section.Note, "help__note");
            foreach (var step in section.Steps)
            {
                AddRow($"{step.Order}. {step.Text}", "help__entry");
            }
        }

        void RenderControls()
        {
            foreach (var entry in _content.Controls.Entries)
            {
                var keys = string.Join(" / ", entry.Keys);
                AddRow($"{entry.Action} ({keys}) — {entry.Description}", "help__entry");
            }
        }

        void RenderTerms()
        {
            foreach (var entry in _content.Terms.Entries)
            {
                AddRow($"{entry.Term} — {entry.Definition}", "help__entry");
            }
        }

        void AddRow(string text, string className)
        {
            var label = new Label(text);
            label.AddToClassList(className);
            _contentContainer.Add(label);
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
                    // docs/20 12.1: Esc는 열린 화면을 한 단계 닫는다 — 시작 화면으로.
                    RaiseBack();
                    evt.StopPropagation();
                    break;
            }
        }

        void ActivateFocused()
        {
            ActivateFocusIndex(_focusedIndex);
        }

        void ActivateFocusIndex(int index)
        {
            SetFocusedIndex(index);

            switch (index)
            {
                case 0:
                    ShowSection(HelpSection.FirstThreeMinutes);
                    break;
                case 1:
                    ShowSection(HelpSection.Controls);
                    break;
                case 2:
                    ShowSection(HelpSection.Terms);
                    break;
                case 3:
                    RaiseBack();
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

        void RaiseBack()
        {
            Back?.Invoke();
        }

        T Resolve<T>(string name) where T : VisualElement
        {
            var element = _root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException($"HelpScreen.uxml is missing the required element '{name}'.");
            }

            return element;
        }
    }
}
