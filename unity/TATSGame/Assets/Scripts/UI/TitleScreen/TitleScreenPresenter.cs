using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.TitleScreen
{
    /// <summary>
    /// TitleScreen.uxml에 바인딩되는 presenter. 상태 보관과 키보드/클릭 입력 처리만 담당하고,
    /// 메뉴 선택 뒤 실제 화면 전환은 T2~T6 구현 전까지 <see cref="MenuItemActivated"/> 이벤트로만 노출한다.
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.2절: presenter는 상태 바인딩과 이벤트 연결만 하고
    /// 교통량·포인트·비용을 계산하지 않는다.
    ///
    /// docs/23_TITLE_SCREEN_BACKLOG.md T7 범위: 서버 연결 표시(연결됨·재시도·끊김), 끊긴 상태에서
    /// `새로 시작`·`이어하기` 비활성화와 사유 표시, 종료 확인. 실제 <c>GET /api/health</c> 호출은
    /// 이 항목의 범위 밖이다 — 저장소에 <c>backend/app/</c> 자체가 없어 health API 구현이 없고,
    /// 응답 필드 계약도 docs/22_TATS_BACKEND_DESIGN_V1.md 318행 "버전 3종 + 프로세스 상태" 한 줄
    /// 설명 밖에는 정의돼 있지 않다(계약 미정). 그래서 <see cref="ReportConnectionStatus"/>는 T3의
    /// <c>ContinuePresenter.ReportResumeSucceeded/Failed</c>와 같은 방식으로, 외부(미래의 health
    /// 어댑터)가 결과를 밀어 넣는 진입점만 제공한다 — 지금은 그걸 호출하는 코드가 없으므로 화면은
    /// 계속 기본값인 Retrying으로 남는다.
    ///
    /// 종료 확인의 진입점은 Esc다. 시작 화면 5개 메뉴(docs/23 T1)에는 별도 `종료` 항목이 없고,
    /// docs/20 12.1은 Esc가 "열린 오버레이·모달을 한 단계 닫는다"고만 정의해 시작 화면처럼 닫을
    /// 오버레이가 없던 상태에서의 Esc 용도를 남겨 두었다 — T1 구현 당시 주석("종료 확인(T7)은 이
    /// 항목의 범위 밖이다")이 예고한 그대로, 여기서는 그 유일한 남는 입력을 종료 확인 오버레이를
    /// 여는 데 쓰기로 했다. 문서가 이 진입점을 명시하지는 않으므로 이는 구현 결정이다.
    /// </summary>
    public sealed class TitleScreenPresenter : IDisposable
    {
        const string FocusedClass = "title-screen__menu-item--focused";
        const string QuitFocusedClass = "title-screen__quit-action--focused";

        const string ConnectedClass = "title-screen__connection-status--connected";
        const string RetryingClass = "title-screen__connection-status--retrying";
        const string DisconnectedClass = "title-screen__connection-status--disconnected";

        enum Mode
        {
            Menu,
            QuitConfirm,
        }

        static readonly TitleScreenMenuItem[] MenuOrder =
        {
            TitleScreenMenuItem.NewGame,
            TitleScreenMenuItem.Continue,
            TitleScreenMenuItem.Settings,
            TitleScreenMenuItem.Help,
            TitleScreenMenuItem.Credits,
        };

        static readonly string[] MenuButtonNames =
        {
            "new-game-button",
            "continue-button",
            "settings-button",
            "help-button",
            "credits-button",
        };

        /// <summary>연결이 끊기면 비활성화되는 메뉴 항목. `새로 시작`·`이어하기`만 대상이다
        /// (docs/23 T7: "연결이 없으면 fixture로 진행하지 않는다") — 환경설정·도움말·기여자는
        /// 서버 세션과 무관해 계속 쓸 수 있다.</summary>
        static readonly bool[] DisabledWhenDisconnected = { true, true, false, false, false };

        readonly VisualElement _root;
        readonly Button[] _menuButtons;

        readonly VisualElement _connectionStatusRoot;
        readonly Label _connectionStatusLabel;
        readonly Label _connectionReasonLabel;

        readonly VisualElement _menuPanel;
        readonly Label _menuDisabledReasonLabel;

        readonly VisualElement _quitConfirmPanel;
        readonly Button _quitCancelButton;
        readonly Button _quitConfirmButton;

        Mode _mode = Mode.Menu;
        Button[] _focusOrder = Array.Empty<Button>();
        int _focusedIndex;
        Button _menuFocusedButtonBeforeQuit;

        TitleConnectionStatus _connectionStatus = TitleConnectionStatus.Retrying;
        bool _disposed;

        /// <summary>메뉴를 고르면 발행한다. 실제 화면 전환은 T2~T6 구현 전까지 이 이벤트로만 노출한다.</summary>
        public event Action<TitleScreenMenuItem> MenuItemActivated;

        /// <summary>종료 확인 오버레이에서 `종료`를 누르면 발행한다. 실제 프로세스 종료 호출은 이
        /// 이벤트를 받는 쪽(View)의 몫이다 — presenter는 UI 상태만 다룬다.</summary>
        public event Action QuitConfirmed;

        public TitleScreenPresenter(VisualElement root)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _menuButtons = new Button[MenuButtonNames.Length];

            for (var i = 0; i < MenuButtonNames.Length; i++)
            {
                var button = _root.Q<Button>(MenuButtonNames[i]);
                if (button == null)
                {
                    throw new InvalidOperationException(
                        $"TitleScreen.uxml is missing the required button '{MenuButtonNames[i]}'.");
                }

                _menuButtons[i] = button;

                var capturedIndex = i;
                button.clicked += () => Activate(capturedIndex);
            }

            _connectionStatusRoot = Resolve<VisualElement>("title-screen-connection-status");
            _connectionStatusLabel = Resolve<Label>("title-screen-connection-label");
            _connectionReasonLabel = Resolve<Label>("title-screen-connection-reason");

            _menuPanel = Resolve<VisualElement>("title-screen-menu-panel");
            _menuDisabledReasonLabel = Resolve<Label>("title-screen-menu-disabled-reason");

            _quitConfirmPanel = Resolve<VisualElement>("title-screen-quit-confirm");
            _quitCancelButton = Resolve<Button>("title-screen-quit-cancel-button");
            _quitConfirmButton = Resolve<Button>("title-screen-quit-confirm-button");

            _quitCancelButton.clicked += CancelQuit;
            _quitConfirmButton.clicked += ConfirmQuit;

            _root.RegisterCallback<KeyDownEvent>(OnKeyDown, TrickleDown.TrickleDown);

            ApplyConnectionStatus();
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

        /// <summary>
        /// 서버 연결 상태를 반영한다. 실제 폴링·<c>GET /api/health</c> 호출은 T7 범위 밖이다 — 클래스
        /// 주석 참고. 끊김(<see cref="TitleConnectionStatus.Disconnected"/>)이면 `새로 시작`·`이어하기`를
        /// 비활성화하고 <paramref name="reason"/>과 고정 사유 문구를 함께 보여준다.
        /// </summary>
        public void ReportConnectionStatus(TitleConnectionStatus status, string reason = null)
        {
            _connectionStatus = status;
            ApplyConnectionStatus(reason);
        }

        void ApplyConnectionStatus(string reason = null)
        {
            _connectionStatusRoot.RemoveFromClassList(ConnectedClass);
            _connectionStatusRoot.RemoveFromClassList(RetryingClass);
            _connectionStatusRoot.RemoveFromClassList(DisconnectedClass);

            string label;
            string appliedClass;
            switch (_connectionStatus)
            {
                case TitleConnectionStatus.Connected:
                    label = "연결됨";
                    appliedClass = ConnectedClass;
                    break;

                case TitleConnectionStatus.Disconnected:
                    label = "연결 끊김";
                    appliedClass = DisconnectedClass;
                    break;

                case TitleConnectionStatus.Retrying:
                default:
                    label = "재시도 중";
                    appliedClass = RetryingClass;
                    break;
            }

            _connectionStatusLabel.text = label;
            _connectionStatusRoot.AddToClassList(appliedClass);

            var disconnected = _connectionStatus == TitleConnectionStatus.Disconnected;

            _connectionReasonLabel.text = disconnected && !string.IsNullOrEmpty(reason) ? reason : string.Empty;
            _connectionReasonLabel.style.display =
                string.IsNullOrEmpty(_connectionReasonLabel.text) ? DisplayStyle.None : DisplayStyle.Flex;

            for (var i = 0; i < _menuButtons.Length; i++)
            {
                if (DisabledWhenDisconnected[i])
                {
                    _menuButtons[i].SetEnabled(!disconnected);
                }
            }

            _menuDisabledReasonLabel.style.display = disconnected ? DisplayStyle.Flex : DisplayStyle.None;

            if (_mode == Mode.Menu)
            {
                RebuildMenuFocusOrder(preserveFocus: true);
            }
        }

        void OnKeyDown(KeyDownEvent evt)
        {
            if (_mode == Mode.QuitConfirm)
            {
                OnQuitConfirmKeyDown(evt);
                return;
            }

            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                    if (_focusOrder.Length > 0)
                    {
                        SetFocusedIndex((_focusedIndex + 1) % _focusOrder.Length, FocusedClass);
                    }

                    evt.StopPropagation();
                    break;

                case KeyCode.UpArrow:
                    if (_focusOrder.Length > 0)
                    {
                        SetFocusedIndex((_focusedIndex - 1 + _focusOrder.Length) % _focusOrder.Length, FocusedClass);
                    }

                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    ActivateFocusedMenuItem();
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    OpenQuitConfirm();
                    evt.StopPropagation();
                    break;
            }
        }

        void OnQuitConfirmKeyDown(KeyDownEvent evt)
        {
            switch (evt.keyCode)
            {
                case KeyCode.DownArrow:
                case KeyCode.UpArrow:
                    // 버튼이 취소·종료 둘뿐이라 상하 화살표 모두 같은 토글로 다룬다.
                    if (_focusOrder.Length > 0)
                    {
                        SetFocusedIndex((_focusedIndex + 1) % _focusOrder.Length, QuitFocusedClass);
                    }

                    evt.StopPropagation();
                    break;

                case KeyCode.Return:
                case KeyCode.KeypadEnter:
                    ActivateFocusedQuitButton();
                    evt.StopPropagation();
                    break;

                case KeyCode.Escape:
                    // docs/20 12.1: Esc는 열린 오버레이를 한 단계 닫는다 — 종료 확인을 취소하고
                    // 메뉴로 돌아간다.
                    CancelQuit();
                    evt.StopPropagation();
                    break;
            }
        }

        void RebuildMenuFocusOrder(bool preserveFocus, Button preferredButton = null)
        {
            var preferred = preferredButton;
            if (preferred == null && preserveFocus && _focusOrder.Length > 0 && _focusedIndex < _focusOrder.Length)
            {
                preferred = _focusOrder[_focusedIndex];
            }

            var enabled = new List<Button>(_menuButtons.Length);
            foreach (var button in _menuButtons)
            {
                if (button.enabledSelf)
                {
                    enabled.Add(button);
                }
            }

            _focusOrder = enabled.ToArray();

            if (_focusOrder.Length == 0)
            {
                return;
            }

            var newIndex = preferred != null ? Array.IndexOf(_focusOrder, preferred) : -1;
            SetFocusedIndex(newIndex >= 0 ? newIndex : 0, FocusedClass);
        }

        void OpenQuitConfirm()
        {
            _menuFocusedButtonBeforeQuit = _focusOrder.Length > 0 && _focusedIndex < _focusOrder.Length
                ? _focusOrder[_focusedIndex]
                : null;

            if (_menuFocusedButtonBeforeQuit != null)
            {
                _menuFocusedButtonBeforeQuit.RemoveFromClassList(FocusedClass);
            }

            _mode = Mode.QuitConfirm;
            _menuPanel.style.display = DisplayStyle.None;
            _quitConfirmPanel.style.display = DisplayStyle.Flex;

            _focusOrder = new[] { _quitCancelButton, _quitConfirmButton };
            // 기본 포커스는 `취소` — ContinuePresenter의 M16 재개 실패 화면과 같은 방어적 기본값으로,
            // 실수로 Enter를 눌러 게임이 종료되는 것을 막는다.
            SetFocusedIndex(0, QuitFocusedClass);
        }

        void CancelQuit()
        {
            _quitCancelButton.RemoveFromClassList(QuitFocusedClass);
            _quitConfirmButton.RemoveFromClassList(QuitFocusedClass);

            _mode = Mode.Menu;
            _quitConfirmPanel.style.display = DisplayStyle.None;
            _menuPanel.style.display = DisplayStyle.Flex;

            RebuildMenuFocusOrder(preserveFocus: true, preferredButton: _menuFocusedButtonBeforeQuit);
        }

        void ConfirmQuit()
        {
            QuitConfirmed?.Invoke();
        }

        void ActivateFocusedQuitButton()
        {
            if (_focusOrder.Length == 0)
            {
                return;
            }

            var focused = _focusOrder[_focusedIndex];
            if (focused == _quitCancelButton)
            {
                CancelQuit();
            }
            else if (focused == _quitConfirmButton)
            {
                ConfirmQuit();
            }
        }

        void SetFocusedIndex(int index, string focusedClass)
        {
            if (_focusOrder.Length == 0)
            {
                return;
            }

            foreach (var button in _focusOrder)
            {
                button.RemoveFromClassList(focusedClass);
            }

            _focusedIndex = Mathf.Clamp(index, 0, _focusOrder.Length - 1);
            var focused = _focusOrder[_focusedIndex];
            focused.AddToClassList(focusedClass);
            focused.Focus();
        }

        void ActivateFocusedMenuItem()
        {
            if (_focusOrder.Length == 0)
            {
                return;
            }

            var focusedButton = _focusOrder[_focusedIndex];
            var index = Array.IndexOf(_menuButtons, focusedButton);
            if (index >= 0)
            {
                Activate(index);
            }
        }

        void Activate(int index)
        {
            if (_mode != Mode.Menu)
            {
                return;
            }

            var button = _menuButtons[index];
            var focusOrderIndex = Array.IndexOf(_focusOrder, button);
            if (focusOrderIndex >= 0)
            {
                SetFocusedIndex(focusOrderIndex, FocusedClass);
            }

            MenuItemActivated?.Invoke(MenuOrder[index]);
        }

        T Resolve<T>(string name) where T : VisualElement
        {
            var element = _root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException($"TitleScreen.uxml is missing the required element '{name}'.");
            }

            return element;
        }
    }
}
