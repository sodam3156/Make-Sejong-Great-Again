using System;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Credits
{
    /// <summary>
    /// CreditsScreen.uxml에 바인딩되는 presenter. docs/23_TITLE_SCREEN_BACKLOG.md T6 범위: 팀 MSGA
    /// 명단·공개 데이터 출처·오픈소스 고지 세 탭을 <see cref="CreditsContentStore"/>가 읽은
    /// <c>credits.json</c> 내용으로 그린다. 본문 문자열은 여기 코드에 없다 — 전부 콘텐츠에서 온다.
    ///
    /// 상하 화살표로 탭 3개와 `뒤로` 사이에서 포커스를 이동하고, Enter로 탭을 전환하거나 `뒤로`를
    /// 활성화한다. 읽기 전용 정보만 보여주는 화면이라 T5 HelpPresenter와 같은 방식으로 탭 전환에
    /// Enter를 재사용했다. Esc는 T1~T5와 같은 방식으로 `뒤로`와 같은 동작을 한다.
    /// </summary>
    public sealed class CreditsPresenter : IDisposable
    {
        const string FocusedClass = "credits__focusable--focused";
        const string ActiveTabClass = "credits__tab--active";

        readonly VisualElement _root;
        readonly CreditsContentStore _store;

        readonly Button _teamTabButton;
        readonly Button _publicDataTabButton;
        readonly Button _openSourceTabButton;
        readonly Button _backButton;
        readonly VisualElement _contentContainer;
        readonly Label _errorLabel;

        readonly Button[] _focusOrder;
        int _focusedIndex;
        CreditsContentDto _content;
        CreditsSection _activeSection = CreditsSection.Team;
        bool _disposed;

        /// <summary>`뒤로` 또는 Esc.</summary>
        public event Action Back;

        public CreditsPresenter(VisualElement root, CreditsContentStore store)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _store = store ?? throw new ArgumentNullException(nameof(store));

            _teamTabButton = Resolve<Button>("credits-tab-team-button");
            _publicDataTabButton = Resolve<Button>("credits-tab-public-data-button");
            _openSourceTabButton = Resolve<Button>("credits-tab-open-source-button");
            _backButton = Resolve<Button>("credits-back-button");
            _contentContainer = Resolve<VisualElement>("credits-content");
            _errorLabel = Resolve<Label>("credits-error-label");

            _focusOrder = new[] { _teamTabButton, _publicDataTabButton, _openSourceTabButton, _backButton };

            _teamTabButton.clicked += () => ActivateFocusIndex(0);
            _publicDataTabButton.clicked += () => ActivateFocusIndex(1);
            _openSourceTabButton.clicked += () => ActivateFocusIndex(2);
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

        /// <summary>credits.json을 다시 읽고 현재 탭을 다시 그린다.</summary>
        public void ReloadContent()
        {
            var result = _store.Load();
            if (result.State == CreditsContentLoadState.Error)
            {
                _content = null;
                _errorLabel.text = $"기여자 정보를 불러오지 못했습니다: {result.FailureReason}";
                _errorLabel.style.display = DisplayStyle.Flex;
                _contentContainer.Clear();
                return;
            }

            _content = result.Content;
            _errorLabel.style.display = DisplayStyle.None;
            ShowSection(_activeSection);
        }

        void ShowSection(CreditsSection section)
        {
            _activeSection = section;

            _teamTabButton.RemoveFromClassList(ActiveTabClass);
            _publicDataTabButton.RemoveFromClassList(ActiveTabClass);
            _openSourceTabButton.RemoveFromClassList(ActiveTabClass);

            _contentContainer.Clear();

            if (_content == null)
            {
                return;
            }

            switch (section)
            {
                case CreditsSection.Team:
                    _teamTabButton.AddToClassList(ActiveTabClass);
                    RenderTeam();
                    break;

                case CreditsSection.PublicDataSources:
                    _publicDataTabButton.AddToClassList(ActiveTabClass);
                    RenderPublicDataSources();
                    break;

                case CreditsSection.OpenSourceNotices:
                    _openSourceTabButton.AddToClassList(ActiveTabClass);
                    RenderOpenSourceNotices();
                    break;
            }
        }

        void RenderTeam()
        {
            var team = _content.Team;
            AddRow(team.Name, "credits__entry");
            foreach (var member in team.Members)
            {
                AddRow(member, "credits__entry");
            }
        }

        void RenderPublicDataSources()
        {
            foreach (var entry in _content.PublicDataSources.Entries)
            {
                var text = string.IsNullOrEmpty(entry.Url)
                    ? entry.Name
                    : $"{entry.Name} — {entry.Url}";
                AddRow(text, "credits__entry");
            }
        }

        void RenderOpenSourceNotices()
        {
            foreach (var entry in _content.OpenSourceNotices.Entries)
            {
                AddRow($"{entry.Name} ({entry.License})", "credits__entry");
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
                    ShowSection(CreditsSection.Team);
                    break;
                case 1:
                    ShowSection(CreditsSection.PublicDataSources);
                    break;
                case 2:
                    ShowSection(CreditsSection.OpenSourceNotices);
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
                throw new InvalidOperationException($"CreditsScreen.uxml is missing the required element '{name}'.");
            }

            return element;
        }
    }
}
